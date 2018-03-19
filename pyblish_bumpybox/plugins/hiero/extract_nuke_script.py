import os

import pyblish.api
import hiero

from bait.paths import get_env_work_file, get_output_path
from bait.deadline import get_render_settings, get_deadline_data
import pipeline_schema
from bait.ftrack.query_runner import QueryRunner


class BumpyboxHieroExtractNukeScript(pyblish.api.InstancePlugin):
    """ Extract Nuke script """

    families = ["nuke"]
    label = "Extract Nuke Script"
    order = pyblish.api.ExtractorOrder + 0.2
    optional = True

    def write_plate_script(self, write_path, item, handles, first_frame_offset, last_frame_offset):
        nuke_writer = hiero.core.nuke.ScriptWriter()

        root_node = hiero.core.nuke.RootNode(first_frame_offset, last_frame_offset)
        nuke_writer.addNode(root_node)

        item.addToNukeScript(script=nuke_writer, firstFrame=first_frame_offset,
                             includeRetimes=True, retimeMethod="Frame",
                             startHandle=handles, endHandle=handles)

        write_node = hiero.core.nuke.WriteNode(write_path)
        write_node.setKnob("file_type", "exr")
        write_node.setKnob("metadata", "all metadata")
        nuke_writer.addNode(write_node)

        data = pipeline_schema.get_data()
        data["extension"] = "nk"

        script_path = pipeline_schema.get_path("temp_file", data)
        nuke_writer.writeToDisk(script_path)

        return script_path

    def get_deadline_plate(self, scene_name, script_path, write_path, component_name, first_frame_offset, last_frame_offset, default_pool):
        return {
            "job": {
                "Plugin": "Nuke",
                "OutputFilename0": write_path,
                "Frames": "{0}-{1}".format(first_frame_offset, last_frame_offset),
                "Name": "{0} - {1}".format(scene_name, component_name),
                "Pool": default_pool
            },
            "plugin": {
                "NukeX": "False",
                "Version": "9.0",
            },
            "auxiliaryFiles": [script_path]
        }

    def process(self, instance):
        scene_name, _ = os.path.splitext(os.path.basename(instance.context.data["currentFile"]))

        runner = QueryRunner()
        default_pool = runner.get_project_department(instance.context.data["ftrackData"]["Project"]["id"])
        runner.close_session()

        task_id = None

        for tag in instance[0].tags():
            task_data = tag.metadata().dict()

            if "task" == task_data.get("tag.family", ""):
                task_id = task_data["tag.id"]

        if task_id is None:
            self.log.warning("No task found to associate nuke script with (Did you tag the shot?)")
            return

        item = instance[0]
        file_path = item.source().mediaSource().fileinfos()[0].filename()
        fps = item.sequence().framerate().toFloat()

        # Get handles.
        handles = 0
        if "handles" in instance.data["families"]:
            for tag in instance[0].tags():
                data = tag.metadata().dict()
                if "handles" == data.get("tag.family", ""):
                    handles = int(data["tag.value"])

        # Get reverse, retime, first and last frame
        reverse = False
        if item.playbackSpeed() < 0:
            reverse = True

        retime = False
        if item.playbackSpeed() != 1.0:
            retime = True

        first_frame = int(item.sourceIn() + 1) - handles
        first_frame_offset = 1
        last_frame = int(item.sourceOut() + 1) + handles
        last_frame_offset = last_frame - first_frame + 1

        if reverse:
            first_frame = int(item.sourceOut() + 1)
            first_frame_offset = 1
            last_frame = int(item.sourceIn() + 1)
            last_frame_offset = last_frame - first_frame + 1

        # Get resolution
        width = item.parent().parent().format().width()
        height = item.parent().parent().format().height()

        component_name = instance.data["name"]
        version = instance.context.data["version"] if "version" in instance.context.data else 1

        output_file = get_output_path(task_id, component_name, version, ".exr")

        script_path = self.write_plate_script(
            write_path=output_file,
            item=item,
            handles=handles,
            first_frame_offset=first_frame_offset,
            last_frame_offset=last_frame_offset
        )
        plate_data = self.get_deadline_plate(
            scene_name=scene_name,
            write_path=output_file,
            script_path=script_path,
            component_name=component_name,
            first_frame_offset=first_frame_offset,
            last_frame_offset=last_frame_offset,
            default_pool=default_pool
        )

        render_settings = get_render_settings('nuke')

        instance.data['deadlineData'] = get_deadline_data(render_settings, plate_data)

        # Creating shot nuke script
        nuke_writer = hiero.core.nuke.ScriptWriter()

        # Root node
        root_node = hiero.core.nuke.RootNode(
            first_frame_offset,
            last_frame_offset,
            fps=fps
        )
        if retime:
            last_frame = abs(int(round(
                last_frame_offset / item.playbackSpeed()
            )))
            root_node = hiero.core.nuke.RootNode(
                first_frame_offset,
                last_frame,
                fps=fps
            )
        fmt = item.parent().parent().format()
        root_node.setKnob("format", "{0} {1}".format(
            fmt.width(),
            fmt.height()
        ))
        nuke_writer.addNode(root_node)

        # Primary read node
        read_node = hiero.core.nuke.ReadNode(
            output_file,
            width=width,
            height=height,
            firstFrame=first_frame,
            lastFrame=last_frame + 1
        )
        read_node.setKnob("frame_mode", 2)
        read_node.setKnob("frame", str(first_frame - 1))
        nuke_writer.addNode(read_node)
        last_node = read_node

        if reverse or retime:

            last_frame = last_frame_offset
            if retime:
                last_frame = abs(int(round(
                    last_frame_offset / item.playbackSpeed()
                )))

            retime_node = hiero.core.nuke.RetimeNode(
                first_frame_offset,
                last_frame_offset,
                first_frame_offset,
                last_frame,
                reverse=reverse
            )
            retime_node.setKnob("shutter", 0)
            retime_node.setInputNode(0, read_node)
            nuke_writer.addNode(retime_node)
            last_node = retime_node

        self.log.info("Extracting deadline data: {}".format(instance.data['deadlineData']))

        data = pipeline_schema.get_data()
        data["extension"] = "exr"
        temp_file = pipeline_schema.get_path("temp_file", data)

        write_node = hiero.core.nuke.WriteNode(temp_file, inputNode=last_node)
        write_node.setKnob("file_type", "exr")
        write_node.setKnob("metadata", "all metadata")
        write_node.setName(str(instance))
        nuke_writer.addNode(write_node)

        # Secondary read nodes
        seq = item.parent().parent()
        time_in = item.timelineIn()
        time_out = item.timelineOut()

        items = []
        for count in range(time_in, time_out):
            items.extend(seq.trackItemsAt(count))

        items = list(set(items))
        items.remove(item)

        last_frame = abs(int(round(last_frame_offset /
                                   item.playbackSpeed())))

        # Re-time node
        for i in items:
            src = i.source().mediaSource().fileinfos()[0].filename()
            in_frame = i.mapTimelineToSource(time_in) + 1 - handles
            out_frame = i.mapTimelineToSource(time_out) + 1 + handles
            read_node = hiero.core.nuke.ReadNode(
                src,
                width=width,
                height=height,
                firstFrame=in_frame,
                lastFrame=out_frame
            )
            nuke_writer.addNode(read_node)

            retime_node = hiero.core.nuke.RetimeNode(
                in_frame,
                out_frame,
                first_frame_offset,
                last_frame
            )
            retime_node.setKnob("shutter", 0)
            retime_node.setInputNode(0, read_node)
            nuke_writer.addNode(retime_node)

        # Get file path
        work_file_path = get_env_work_file("nuke", task_id, "nk", 1)

        # Create directories
        if not os.path.exists(os.path.dirname(work_file_path)):
            os.makedirs(os.path.dirname(work_file_path))

        # Create nuke script
        nuke_writer.writeToDisk(work_file_path)

        self.log.info("Writing Nuke script to: \"%s\"" % work_file_path)