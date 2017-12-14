import math

import hou
import pyblish.api
from bait.deadline import get_render_settings, get_deadline_data, increase_chunk_size, format_frames
from bait.ftrack.query_runner import QueryRunner


class BumpyboxDeadlineExtractHoudini(pyblish.api.InstancePlugin):
    """ Appending Deadline data to deadline instances. """

    families = ["deadline"]
    order = pyblish.api.ExtractorOrder
    label = "Deadline"
    hosts = ["houdini"]

    def process(self, instance):

        node = instance[0]
        collection = instance.data["collection"]

        existing_data = instance.data.get(
            "deadlineData", {"job": {}, "plugin": {}}
        )

        render_settings = get_render_settings("houdini")
        runner = QueryRunner()
        default_pool = runner.get_project_department(instance.context.data["ftrackData"]["Project"]["id"])
        existing_data["job"]["Pool"] = default_pool

        data = get_deadline_data(render_settings, existing_data)

        # Setting job data.
        data["job"]["Plugin"] = "Houdini"

        # Replace houdini frame padding with Deadline padding
        fmt = "{head}" + "#" * collection.padding + "{tail}"
        data["job"]["OutputFilename0"] = collection.format(fmt)

        # Frame range
        start_frame = int(node.parm("f1").eval())
        end_frame = int(node.parm("f2").eval())
        step_frame = int(node.parm("f3").eval())

        if node.parm("trange").eval() == 0:
            start_frame = end_frame = int(hou.frame())

        data["job"]["Frames"] = format_frames(start_frame, end_frame, step_frame)

        data['job']['ChunkSize'] = increase_chunk_size(
            start_frame, end_frame, data["job"]["ChunkSize"], step_frame
        )

        # Setting plugin data
        data["plugin"]["OutputDriver"] = node.path()
        data["plugin"]["Version"] = str(hou.applicationVersion()[0])
        data["plugin"]["SceneFile"] = instance.context.data["currentFile"]

        instance.data["deadlineData"] = data
