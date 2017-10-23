import math

import nuke
import pyblish.api
import os
from bait.paths import get_output_path


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

        data = instance.data.get("deadlineData", {"job": {}, "plugin": {}})

        # Setting job data.
        data["job"]["Plugin"] = "Nuke"
        data["job"]["Priority"] = int(instance.data["deadlinePriority"])
        data["job"]["Pool"] = instance.data["deadlinePool"]
        data["job"]["Group"] = instance.data["deadlineGroup"]
        data["job"]["ConcurrentTasks"] = int(
            instance.data["deadlineConcurrentTasks"]
        )
        data["job"]["LimitGroups"] = instance.data["deadlineLimits"]

        # Replace houdini frame padding with Deadline padding
        fmt = "{head}" + "#" * collection.padding + "{tail}"
        output_sequence = os.path.basename(collection.format(fmt))

        task_id = instance.context.data["ftrackData"]["Task"]["id"]
        component_name = instance.data["name"]
        version = instance.context.data["version"]
        _, ext = os.path.splitext(output_sequence)

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

        data["job"]["Frames"] = "{0}-{1}".format(
            int(first_frame), int(last_frame)
        )

        # Chunk size
        data["job"]["ChunkSize"] = int(instance.data["deadlineChunkSize"])
        if len(list(collection)) == 1:
            data["job"]["ChunkSize"] = str(int(last_frame))
        else:
            tasks = last_frame - first_frame + 1.0
            chunks = last_frame - first_frame + 1.0
            chunks /= data["job"]["ChunkSize"]
            # Deadline can only handle 5000 tasks maximum
            if tasks > 5000 and chunks > 5000:
                data["job"]["ChunkSize"] = str(int(math.ceil(tasks / 5000.0)))

        # Setting plugin data
        data["plugin"]["SceneFile"] = instance.context.data["currentFile"]
        data["plugin"]["EnforceRenderOrder"] = True
        data["plugin"]["WriteNode"] = node.name()
        data["plugin"]["NukeX"] = nuke.env["nukex"]
        data["plugin"]["Version"] = nuke.NUKE_VERSION_STRING.split("v")[0]
        data["plugin"]["EnablePathMapping"] = False

        # Setting data
        instance.data["deadlineData"] = data
