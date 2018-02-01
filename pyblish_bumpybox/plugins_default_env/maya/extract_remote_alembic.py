import os

import pymel
import pyblish.api
import maya.cmds as cmds

from bait.paths import get_cache_output_path
from bait.deadline import format_frames, get_render_settings, get_deadline_data


class MayaExtractRemoteAlembic(pyblish.api.InstancePlugin):
    """ Extracts alembic files using deadline. """

    order = pyblish.api.ExtractorOrder + 0.1
    families = ["alembic"]
    optional = True
    label = "Remote Alembic"
    hosts = ["maya"]

    def process(self, instance):
        if "local" in instance.data["families"]:
            return

        # Generate export command.
        frame_start = int(pymel.core.playbackOptions(q=True, min=True))
        frame_end = int(pymel.core.playbackOptions(q=True, max=True))

        render_settings = get_render_settings("alembic")

        deadline_arguments = instance.data.get(
            "deadlineData", {"job": {}, "plugin": {}}
        )
        deadline_arguments['job']['frames'] = format_frames(frame_start, frame_end)

        deadline_arguments['plugin']['WriteVisibility'] = True

        component_name = instance.data["name"]
        version = instance.context.data["version"]
        task_id = instance.context.data['ftrackTask']['id']

        output_path = get_cache_output_path(task_id, component_name, version, ".abc")

        output_dir = os.path.dirname(output_path)
        output_file = os.path.basename(output_path)

        deadline_arguments["job"]["Plugin"] = "MayaBatch"
        deadline_arguments['job']['OutputFilename0'] = output_path

        deadline_arguments['plugin']['AlembicSelection'] = instance[0][0].name()
        deadline_arguments['plugin']['OutputFilePath'] = output_dir
        deadline_arguments['plugin']['OutputFile'] = output_file

        deadline_arguments['plugin']['Camera'] = ""
        deadline_arguments['plugin']['Camera0'] = ""
        deadline_arguments['plugin']['SceneFile'] = instance.context.data['currentFile']

        for index, camera in enumerate(cmds.listCameras()):
            deadline_arguments['plugin']['Camera{}'.format(index + 1)] = camera

        self.log.info("Output Dir: {}".format(output_dir))
        self.log.info("Output File: {}".format(output_file))
        self.log.info("Item names: {}".format(instance[0]))

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Call deadline
        instance.data['deadlineData'] = get_deadline_data(render_settings, deadline_arguments)
