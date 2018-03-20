import math
import os

import pymel.core
from pymel import versions

import pyblish.api
from bait.paths import get_output_path
from bait.deadline import get_render_settings, get_deadline_data, increase_chunk_size, format_frames
from bait.ftrack.query_runner import QueryRunner


class ExtractDeadlineMaya(pyblish.api.InstancePlugin):
    """ Appending Deadline data to deadline instances. """

    families = ["deadline"]
    order = pyblish.api.ExtractorOrder
    label = "Deadline"
    hosts = ["maya"]

    def process(self, instance):

        collection = instance.data["collection"]

        existing_data = instance.data.get(
            "deadlineData", {"job": {}, "plugin": {}}
        )

        runner = QueryRunner()
        default_pool = runner.get_project_department(instance.context.data["ftrackData"]["Project"]["id"])
        existing_data["job"]["Pool"] = default_pool
        runner.close_session()

        current_renderer = pymel.core.getAttr("defaultRenderGlobals.currentRenderer")
        render_settings = get_render_settings("maya", current_renderer)

        data = get_deadline_data(render_settings, existing_data)

        data["job"]["Plugin"] = "MayaBatch"

        # Replace houdini frame padding with Deadline padding
        fmt = "{head}" + "#" * collection.padding + "{tail}"
        output_sequence = os.path.basename(collection.format(fmt))
        _, ext = os.path.splitext(output_sequence)

        task_id = instance.context.data["ftrackData"]["Task"]["id"]
        component_name = instance.data["name"]
        version = instance.context.data["version"]

        output_file = get_output_path(task_id, component_name, version, ext)
        output_folder = os.path.dirname(output_file)

        data["job"]["OutputFilename0"] = os.path.join(output_folder, output_sequence)

        # Frame range
        render_globals = pymel.core.PyNode("defaultRenderGlobals")
        start_frame = int(render_globals.startFrame.get())
        end_frame = int(render_globals.endFrame.get())
        step_frame = int(render_globals.byFrameStep.get())

        data["job"]["Frames"] = format_frames(start_frame, end_frame, step_frame)

        data['job']['ChunkSize'] = increase_chunk_size(
            start_frame, end_frame, data["job"]["ChunkSize"], step_frame
        )

        scene_file = instance.context.data["currentFile"]

        data["plugin"]["SceneFile"] = scene_file
        data["plugin"]["ProjectPath"] = os.path.dirname(scene_file)
        data["plugin"]["OutputFilePath"] = os.path.dirname(output_folder)
        data["plugin"]["RenderLayer"] = instance[0].name()
        data["plugin"]["Version"] = versions.flavor()

        # Setting data
        instance.data["deadlineData"] = data
