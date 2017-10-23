import math
import os

import pymel.core
from pymel import versions

import pyblish.api
from bait.paths import get_output_path


class BumpyboxDeadlineExtractMaya(pyblish.api.InstancePlugin):
    """ Appending Deadline data to deadline instances. """

    families = ["deadline"]
    order = pyblish.api.ExtractorOrder
    label = "Deadline"
    hosts = ["maya"]

    def process(self, instance):

        collection = instance.data["collection"]

        data = instance.data.get(
            "deadlineData", {"job": {}, "plugin": {}}
        )

        # Setting job data.
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

        data["job"]["Priority"] = instance.data["deadlinePriority"]
        data["job"]["Pool"] = instance.data["deadlinePool"]
        value = instance.data["deadlineConcurrentTasks"]
        data["job"]["ConcurrentTasks"] = value
        data["job"]["LimitGroups"] = instance.data["deadlineLimits"]
        data["job"]["Group"] = instance.data["deadlineGroup"]

        # Frame range
        render_globals = pymel.core.PyNode("defaultRenderGlobals")
        start_frame = int(render_globals.startFrame.get())
        end_frame = int(render_globals.endFrame.get())
        step_frame = int(render_globals.byFrameStep.get())

        data["job"]["Frames"] = "{0}-{1}x{2}".format(
            start_frame, end_frame, step_frame
        )

        # Chunk size
        data["job"]["ChunkSize"] = instance.data["deadlineChunkSize"]
        if len(list(collection)) == 1:
            data["job"]["ChunkSize"] = str(end_frame)
        else:
            tasks = (end_frame - start_frame + 1.0) / step_frame
            chunks = (end_frame - start_frame + 1.0) / data["job"]["ChunkSize"]
            # Deadline can only handle 5000 tasks maximum
            if tasks > 5000 and chunks > 5000:
                data["job"]["ChunkSize"] = str(int(math.ceil(tasks / 5000.0)))

        # Setting plugin data
        current_renderer = pymel.core.getAttr("defaultRenderGlobals.currentRenderer")

        data["plugin"]["Renderer"] = "file"
        data["plugin"]["UsingRenderLayers"] = 1
        data["plugin"]["RenderLayer"] = instance[0].name()
        data["plugin"]["Version"] = versions.flavor()
        data["plugin"]["UseLegacyRenderLayers"] = 1
        data["plugin"]["MaxProcessors"] = 0

        scene_file = instance.context.data["currentFile"]
        data["plugin"]["SceneFile"] = scene_file
        data["plugin"]["ProjectPath"] = os.path.dirname(scene_file)
        data["plugin"]["OutputFilePath"] = os.path.dirname(output_folder)

        if current_renderer == "redshift":
            data['plugin']['Renderer'] = 'redshift'
            data['plugin']['RedshiftVerbose'] = 2
            data["plugin"]["Animation"] = 1
            data["plugin"]["StrictErrorChecking"] = 0

        # Arnold plugin settings
        if "arnold" in instance.data.get("families", []):
            data["plugin"]["Renderer"] = "arnold"
            data["plugin"]["ArnoldVerbose"] = 1
            data["plugin"]["Animation"] = 1

        # Setting data
        instance.data["deadlineData"] = data
