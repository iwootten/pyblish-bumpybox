import pyblish.api


class BumpyboxDeadlineExtractSuspended(pyblish.api.InstancePlugin):
    """ Option to suspend Deadline job on submission """

    order = pyblish.api.ExtractorOrder
    label = "Suspend Deadline Job Initially"
    families = ["deadline"]
    active = False
    optional = True

    def process(self, instance):
        deadline_data = instance.data.get(
            "deadlineData", {"job": {}, "plugin": {}}
        )

        deadline_data["job"]["InitialStatus"] = "Suspended"

        instance.data["deadlineData"] = deadline_data
