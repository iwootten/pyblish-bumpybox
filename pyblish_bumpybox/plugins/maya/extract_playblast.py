import pyblish.api
from capture import capture


class BumpyboxMayaExtractPlayblast(pyblish.api.InstancePlugin):
    """ Extracts playblast. """

    order = pyblish.api.ExtractorOrder
    families = ["playblast"]
    optional = True
    label = "Playblast"
    hosts = ["maya"]

    def process(self, instance):

        filename = list(instance.data["collection"])[0]
        filename = filename.replace(
            instance.data["collection"].format("{tail}"),
            ""
        )

        kwargs = {
            'filename': filename,
            'viewer': False,
            'show_ornaments': False,
            'overwrite': True,
            'off_screen': True,
            'viewport_options': {
                 "rendererName": "vp2Renderer"
            },
            'viewport2_options': {
                "multiSampleEnable": True,
                "multiSampleCount": 8
            },
            'camera_options': {
                "panZoomEnabled": False
            }
        }

        if 'audio' in instance.context.data and instance.context.data['audio']['enabled']:
            kwargs['sound'] = instance.context.data['audio']['node']

        capture(
            instance[0].getTransform().name(),
            **kwargs
        )
