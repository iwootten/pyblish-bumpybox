import os

import pyblish.api
import pyblish_aftereffects


class AppendDeadlineData(pyblish.api.InstancePlugin):
    """ Appending Deadline data to farm related instances """

    families = ["img.farm.*"]
    label = "Deadline"
    order = pyblish.api.ExtractorOrder

    def process(self, instance):

        job_data = {}
        plugin_data = {}
        if "deadlineData" in instance.data:
            job_data = instance.data["deadlineData"]["job"].copy()
            plugin_data = instance.data["deadlineData"]["plugin"].copy()

        # setting plugin data
        plugin_data["SceneFile"] = instance.context.data["currentFile"]
        plugin_data["Comp"] = str(instance)

        app_version = pyblish_aftereffects.send("return app.version")
        app_major_version = ".".join(app_version.split("x")[0].split(".")[:2])
        plugin_data["Version"] = app_major_version

        # setting job data
        job_data["Plugin"] = "AfterEffects"

        index = instance.data["index"]
        cmd = "return app.project.renderQueue.item({0}).comp.frameDuration"
        frame_duration = pyblish_aftereffects.send(cmd.format(index))
        frame_duration = float(frame_duration)

        cmd = "return app.project.renderQueue.item({0}).timeSpanStart"
        time_start = float(pyblish_aftereffects.send(cmd.format(index)))
        first_frame = time_start * (1 / frame_duration)

        cmd = "return app.project.renderQueue.item({0}).timeSpanDuration"
        time_duration = float(pyblish_aftereffects.send(cmd.format(index)))
        last_frame = (time_duration * (1 / frame_duration)) - 1

        job_data["Frames"] = "{0}-{1}".format(int(first_frame),
                                              int(last_frame))

        name = os.path.basename(instance.context.data["currentFile"])
        name = os.path.splitext(name)[0]
        job_data["Name"] = name + " - " + str(instance)

        output = instance.data["output"].replace("[", "").replace("]", "")
        job_data["OutputFilename0"] = output

        job_data["Pool"] = "medium"
        group = "aftereffects_{0}".format(app_major_version.replace(".", "_"))
        job_data["Group"] = group
        job_data["LimitGroups"] = "aftereffects"
        job_data["ChunkSize"] = "10"

        # setting data
        data = {"job": job_data, "plugin": plugin_data}
        instance.data["deadlineData"] = data