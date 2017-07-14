import pymel.core

import pyblish.api


class BumpyboxDeadlineRepairParameters(pyblish.api.Action):

    label = "Repair"
    icon = "wrench"
    on = "failed"

    def process(self, context, plugin):

        # Get the errored instances
        failed = []
        for result in context.data["results"]:
            if (result["error"] is not None and
               result["instance"] is not None and
               result["instance"] not in failed):
                failed.append(result["instance"])

        # Apply pyblish.logic to get the instances for the plug-in.
        instances = pyblish.api.instances_by_plugin(failed, plugin)

        plugin = plugin()
        for instance in instances:

            node = instance[0]

            if not hasattr(node, "deadlineChunkSize"):
                pymel.core.addAttr(node,
                                   longName="deadlineChunkSize",
                                   defaultValue=10,
                                   attributeType="long")
                attr = pymel.core.Attribute(node.name() + ".deadlineChunkSize")
                pymel.core.setAttr(attr, channelBox=True)

            if not hasattr(node, "deadlinePriority"):
                pymel.core.addAttr(node,
                                   longName="deadlinePriority",
                                   defaultValue=50,
                                   attributeType="long")
                attr = pymel.core.Attribute(node.name() + ".deadlinePriority")
                pymel.core.setAttr(attr, channelBox=True)

            if not hasattr(node, "deadlinePool"):
                pymel.core.addAttr(node,
                                   longName="deadlinePool",
                                   dataType="string")
                attr = pymel.core.Attribute(node.name() + ".deadlinePool")
                pymel.core.setAttr(attr, "medium", channelBox=True)

            if not hasattr(node, "deadlineConcurrentTasks"):
                pymel.core.addAttr(node,
                                   longName="deadlineConcurrentTasks",
                                   defaultValue=1,
                                   attributeType="long")
                attr = pymel.core.Attribute(
                    node.name() + ".deadlineConcurrentTasks"
                )
                pymel.core.setAttr(attr, channelBox=True)

            if not hasattr(node, "deadlineGroup"):
                pymel.core.addAttr(node,
                                   longName="deadlineGroup",
                                   dataType="string")
                attr = pymel.core.Attribute(
                    node.name() + ".deadlineGroup"
                )
                pymel.core.setAttr(attr, "maya", channelBox=True)

            if not hasattr(node, "deadlineLimits"):
                current_renderer = pymel.core.getAttr("defaultRenderGlobals.currentRenderer")

                pymel.core.addAttr(node,
                                   longName="deadlineLimits",
                                   dataType="string")
                attr = pymel.core.Attribute(
                    node.name() + ".deadlineLimits"
                )
                pymel.core.setAttr(attr, current_renderer, channelBox=True)


class BumpyboxDeadlineValidateMayaParameters(pyblish.api.InstancePlugin):
    """ Validates the existence of deadline parameters on node. """

    order = pyblish.api.ValidatorOrder
    label = "Parameters"
    families = ["deadline"]
    hosts = ["maya"]
    actions = [BumpyboxDeadlineRepairParameters]

    def process(self, instance):

        node = instance[0]

        msg = "Could not find Chunk Size on node \"{0}\"".format(node)
        assert "deadlineChunkSize" in instance.data, msg

        msg = "Could not find Priority on node \"{0}\"".format(node)
        assert "deadlinePriority" in instance.data, msg

        msg = "Could not find Pool on node \"{0}\"".format(node)
        assert "deadlinePool" in instance.data, msg

        msg = "Could not find Concurrent Tasks on node \"{0}\"".format(node)
        assert "deadlineConcurrentTasks" in instance.data, msg

        msg = "Could not find Group on node \"{0}\"".format(node)
        assert "deadlineGroup" in instance.data, msg

        msg = "Could not find Limit Groups on node \"{0}\"".format(node)
        assert "deadlineLimits" in instance.data, msg
