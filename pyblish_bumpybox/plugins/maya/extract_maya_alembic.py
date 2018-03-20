import os

import pymel
import pyblish.api


class ExtractMayaAlembic(pyblish.api.InstancePlugin):
    """ Extracts alembic files. """

    order = pyblish.api.ExtractorOrder
    families = ["alembic"]
    optional = True
    label = "Alembic"
    hosts = ["maya"]

    def process(self, instance):

        # Validate whether we can strip namespaces.
        nodesString = ""
        stripNamespaces = True
        root_names = []
        for member in instance[0]:
            nodesString += "-root %s " % member.name()
            if member.name().split(":")[-1] not in root_names:
                root_names.append(member.name().split(":")[-1])
            else:
                stripNamespaces = False

        # Generate export command.
        frame_start = int(pymel.core.playbackOptions(q=True, min=True))
        frame_end = int(pymel.core.playbackOptions(q=True, max=True))

        cmd = "-frameRange %s %s" % (frame_start, frame_end)
        if stripNamespaces:
            cmd += " -stripNamespaces"
        else:
            msg = "Can't strip namespaces, because of conflicting root names."
            msg += " Nodes will be renamed."
            self.log.warning(msg)

        cmd += " -uvWrite -worldSpace -wholeFrameGeo -eulerFilter -writeFaceSets -writeUVSets "
        cmd += "-writeVisibility {0} ".format(nodesString)
        path = list(instance.data["collection"])[0].replace("\\", "/")
        cmd += "-file \"{0}\"".format(path)

        # Ensure output directory exists.
        path = os.path.dirname(list(instance.data["collection"])[0])
        if not os.path.exists(path):
            os.makedirs(path)

        # Turn off viewport updating while exporting.
        pymel.core.general.refresh(suspend=True)
        try:
            pymel.core.AbcExport(j=cmd)
        except Exception as e:
            raise e
        pymel.core.general.refresh(suspend=False)
