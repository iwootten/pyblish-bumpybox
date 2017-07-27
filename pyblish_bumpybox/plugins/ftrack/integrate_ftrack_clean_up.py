import os

import pyblish.api
import clique


class BumpyboxIntegrateFtrackCleanUp(pyblish.api.InstancePlugin):
    """ Clean up any workspace files that has been integrated.

    Offset to get component from pyblish-ftrack
    """

    order = pyblish.api.IntegratorOrder + 0.1
    label = "Ftrack Clean Up"
    families = ["ftrack"]
    optional = True

    def process(self, instance):

        for data in instance.data.get("ftrackComponentsList", []):
            path = data["component_path"]

            # Iterates all published components and removes those that
            # are within collection
            if "component" in data and "workspace" in path:
                if os.path.exists(path):
                    # This is a file component which needs removing
                    os.remove(path)
                else:
                    collection = clique.parse(path)
                    for f in collection:
                        os.remove(f)
                        self.log.info("Deleted: \"{0}\"".format(f))
