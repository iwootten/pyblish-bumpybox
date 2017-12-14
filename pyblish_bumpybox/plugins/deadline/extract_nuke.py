import nuke
import pyblish.api
import os
from bait.paths import get_output_path
from bait.deadline import get_render_settings, get_deadline_data, format_frames, increase_chunk_size
from bait.ftrack.query_runner import QueryRunner


class BumpyboxDeadlineExtractNuke(pyblish.api.InstancePlugin):
    """ Appending Deadline data to deadline instances.

    Important that Path Mapping is turned off in the Nuke plugin.
    """

    families = ["deadline"]
    order = pyblish.api.ExtractorOrder
    label = "Deadline"
    hosts = ["nuke"]

    def process(self, instance):

        collection = instance.data["collection"]

        render_settings = get_render_settings("nuke")

        existing_data = instance.data.get(
            "deadlineData", {"job": {}, "plugin": {}}
        )

        runner = QueryRunner()
        default_pool = runner.get_project_department(instance.context.data["ftrackData"]["Project"]["id"])
        existing_data["job"]["Pool"] = default_pool

        data = get_deadline_data(render_settings, existing_data)

        # Setting job data.
        data["job"]["Plugin"] = "Nuke"

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

        # Get frame range
        node = instance[0]
        first_frame = nuke.root()["first_frame"].value()
        last_frame = nuke.root()["last_frame"].value()

        if node["use_limit"].value():
            first_frame = node["first"].value()
            last_frame = node["last"].value()

        data["job"]["Frames"] = format_frames(first_frame, last_frame)

        data['job']['ChunkSize'] = increase_chunk_size(
            int(first_frame), int(last_frame), data["job"]["ChunkSize"]
        )

        # Setting plugin data
        data["plugin"]["SceneFile"] = instance.context.data["currentFile"]
        data["plugin"]["WriteNode"] = node.name()
        data["plugin"]["NukeX"] = nuke.env["nukex"]
        data["plugin"]["Version"] = nuke.NUKE_VERSION_STRING.split("v")[0]

        # Setting data
        instance.data["deadlineData"] = data
