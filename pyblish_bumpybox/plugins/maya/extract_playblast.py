import pyblish.api
from capture import capture
import os
import subprocess
import importlib
from bait.ftrack.query_runner import QueryRunner


class BumpyboxMayaExtractPlayblast(pyblish.api.InstancePlugin):
    """ Extracts playblast. """

    order = pyblish.api.ExtractorOrder
    families = ["playblast"]
    optional = True
    label = "Playblast"
    hosts = ["maya"]

    def process(self, instance):
        collection = instance.data["collection"]

        pipeline_env = os.getenv("PIPELINE_ENV", "dev")
        settings = importlib.import_module("config.{}".format(pipeline_env))

        filename_with_burnin = list(collection)[0]
        collection_without_burnin = filename_with_burnin.replace(collection.format("{tail}"), "_notext")
        filename_without_burnin = "{}.mov".format(collection_without_burnin)

        kwargs = {
            'filename': collection_without_burnin,
            'viewer': False,
            'show_ornaments': False,
            'overwrite': True,
            'off_screen': True,
            'viewport_options': {
                 "rendererName": "vp2Renderer"
            },
            'viewport2_options': {
                "multiSampleEnable": True,
                "multiSampleCount": 8,
                "ssaoEnable": True,
                "lineAAEnable": True
            },
            'camera_options': {
                "panZoomEnabled": False
            }
        }

        if 'audio' in instance.context.data and instance.context.data['audio']['enabled']:
            kwargs['sound'] = instance.context.data['audio']['node']

        # Create quicktime from viewport settings
        capture(
            instance[0].getTransform().name(),
            **kwargs
        )

        # Add text to the quicktime created
        query_runner = QueryRunner()
        task = query_runner.get_task(instance.context.data['ftrackData']['Task']['id'])
        parents = query_runner.get_parents(task)

        shotname = ""

        for parent in parents:
            if 'object_type' in parent and parent['object_type']['name'] == 'Shot':
                shotname = parent['name']

        query_runner.close_session()

        network_tools_path = settings.networked_tools_dir
        font_path = os.path.join(network_tools_path, "ffmpeg", "fonts", "OpenSans-Regular.ttf")
        font_drive, font_tail = os.path.splitdrive(font_path)
        font_path = "{}\\\\:/{}".format(font_drive.strip(":"), font_tail.strip("\\").replace("\\", "/"))

        text_string = "[in]drawtext=fontfile={}:text='{}':x=50:y=50: fontcolor=white:fontsize=24, " \
                      "drawtext=fontfile={}:text=%{{eif\\\\:n+1\\\\:d}}:x=50:y=(h-th)-50:fontcolor=white:fontsize=24[out]"\
            .format(font_path, shotname, font_path)

        ffmpeg_args = [
            "{}\\ffmpeg\\bin\\ffmpeg.exe".format(network_tools_path), "-i", filename_without_burnin,
            "-y",
            "-vf", text_string,
            "-crf", "1",
            "-refs", "1",
            "-codec:a", "copy",
            "-x264opts", "b-pyramid=0",
            filename_with_burnin
        ]

        subprocess.call(ffmpeg_args)
