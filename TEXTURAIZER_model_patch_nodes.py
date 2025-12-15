import torch
import torch.nn.functional as F
from torch.nn.modules.utils import _pair


# -----------------------------
# Model seamless tiling patch
# -----------------------------

def conv_forward(lyr, tensor, weight, bias):
    step = lyr.timestep
    in_range = (lyr.paddingStartStep < 0 or step >= lyr.paddingStartStep) and (
        lyr.paddingStopStep < 0 or step <= lyr.paddingStopStep
    )

    if in_range:
        working = F.pad(tensor, lyr.paddingX, mode=lyr.padding_modeX)
        working = F.pad(working, lyr.paddingY, mode=lyr.padding_modeY)
    else:
        working = F.pad(tensor, lyr.paddingX, mode="constant")
        working = F.pad(working, lyr.paddingY, mode="constant")

    lyr.timestep += 1

    return F.conv2d(
        working, weight, bias, lyr.stride, _pair(0), lyr.dilation, lyr.groups
    )


class Texturaizer_SeamlessTilingPatch:
    """
    Applies the SD seamless-tiling hack by switching Conv2d padding to circular
    within a configurable step range. Experimental.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model": ("MODEL",),
                "startStep": ("INT", {"default": 0}),
                "stopStep": ("INT", {"default": 999}),
                "tilingX": ("BOOLEAN", {"default": True}),
                "tilingY": ("BOOLEAN", {"default": True}),
            }
        }

    RETURN_TYPES = ("MODEL",)
    FUNCTION = "apply"
    CATEGORY = "Texturaizer"

    def _iter_conv2d_layers(self, model_root):
        for layer in model_root.modules():
            if isinstance(layer, torch.nn.Conv2d):
                yield layer

    def _patch_conv_layer(self, layer, start_step, stop_step, tile_x, tile_y):
        layer.padding_modeX = "circular" if tile_x else "constant"
        layer.padding_modeY = "circular" if tile_y else "constant"

        layer.paddingX = (
            layer._reversed_padding_repeated_twice[0],
            layer._reversed_padding_repeated_twice[1],
            0,
            0,
        )
        layer.paddingY = (
            0,
            0,
            layer._reversed_padding_repeated_twice[2],
            layer._reversed_padding_repeated_twice[3],
        )

        layer.paddingStartStep = start_step
        layer.paddingStopStep = stop_step
        layer.timestep = 0

        layer._conv_forward = conv_forward.__get__(layer, torch.nn.Conv2d)

    def apply(self, model, startStep, stopStep, tilingX, tilingY):
        for layer in self._iter_conv2d_layers(model.model):
            self._patch_conv_layer(layer, startStep, stopStep, tilingX, tilingY)
        return (model,)


# -----------------------------
# Circular VAE decode
# -----------------------------

def _vae_conv2d_forward(self, input, weight, bias):
    working = F.pad(input, self.paddingX, mode=self.padding_modeX)
    working = F.pad(working, self.paddingY, mode=self.padding_modeY)
    return F.conv2d(working, weight, bias, self.stride, _pair(0), self.dilation, self.groups)


def texturaizer_make_circular_asymm(model, tile_x, tile_y):
    for layer in (l for l in model.modules() if isinstance(l, torch.nn.Conv2d)):
        layer.padding_modeX = "circular" if tile_x else "constant"
        layer.padding_modeY = "circular" if tile_y else "constant"
        layer.paddingX = (
            layer._reversed_padding_repeated_twice[0],
            layer._reversed_padding_repeated_twice[1],
            0,
            0,
        )
        layer.paddingY = (
            0,
            0,
            layer._reversed_padding_repeated_twice[2],
            layer._reversed_padding_repeated_twice[3],
        )
        layer._conv_forward = _vae_conv2d_forward.__get__(layer, torch.nn.Conv2d)
    return model


class Texturaizer_CircularVAEDecode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "samples": ("LATENT",),
                "vae": ("VAE",),
                "tiling": (["enable", "x_only", "y_only", "disable"],),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "decode"
    CATEGORY = "Texturaizer"

    def decode(self, samples, vae, tiling):
        # This patches the provided VAE instance in-place (persists for reuse of this VAE object).
        if tiling == "enable":
            texturaizer_make_circular_asymm(vae.first_stage_model, True, True)
        elif tiling == "x_only":
            texturaizer_make_circular_asymm(vae.first_stage_model, True, False)
        elif tiling == "y_only":
            texturaizer_make_circular_asymm(vae.first_stage_model, False, True)
        else:
            texturaizer_make_circular_asymm(vae.first_stage_model, False, False)

        return (vae.decode(samples["samples"]),)


NODE_CLASS_MAPPINGS = {
    "Texturaizer_SeamlessTilingPatch": Texturaizer_SeamlessTilingPatch,
    "Texturaizer_CircularVAEDecode": Texturaizer_CircularVAEDecode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Texturaizer_SeamlessTilingPatch": "Seamless Tiling Patch (Texturaizer)",
    "Texturaizer_CircularVAEDecode": "Circular VAE Decode (Texturaizer)",
}
