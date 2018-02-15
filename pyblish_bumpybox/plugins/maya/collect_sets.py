import os

import pyblish.api
import pymel.core as pm
import clique


class BumpyboxMayaCollectSets(pyblish.api.ContextPlugin):
    """ Collects all sets in scene """

    order = pyblish.api.CollectorOrder
    label = "Sets"
    hosts = ["maya"]
    extensions = {
        "mayaAscii": "ma", "mayaBinary": "mb", "alembic": "abc"
    }
    family_mappings = {
        "mayaAscii": "scene", "mayaBinary": "scene", "alembic": "cache"
    }
    invalid_sets = [
        "lightEditorRoot", "defaultLightSet", "defaultObjectSet"
    ]

    def validate_set(self, object_set):

        for member in object_set.members():
            if member.nodeType() in ["transform", "renderLayer"]:
                return True

        return False

    def get_instance_data(self, object_set, fmt, instance_type):
        name = object_set.name().replace(":", "_")

        data = {
            "families": [fmt, self.family_mappings[fmt], instance_type],
            "label": "{0} - {1} - {2}".format(name, fmt, instance_type),
            "publish": True
        }

        if hasattr(object_set, fmt):
            attr = pm.Attribute(object_set.name() + "." + fmt)
            data["publish"] = attr.get()

        return data

    def generate_collection(self, current_file, fmt, name):
        # Generate collection
        filename, _ = os.path.splitext(os.path.basename(current_file))
        path = os.path.join(
            os.path.dirname(current_file),
            "workspace", filename
        )
        head = "{0}_{1}.".format(path, name)
        tail = "." + self.extensions[fmt]
        collection = clique.Collection(head=head, padding=4, tail=tail)

        frame_start = int(
            pm.playbackOptions(query=True, minTime=True)
        )
        collection.add(head + str(frame_start).zfill(4) + tail)

        return collection

    def process(self, context):

        # Collect sets named starting with "remote".
        remote_members = []

        for object_set in pm.ls(type="objectSet"):
            if object_set.name().startswith("remote"):
                remote_members.extend(object_set.members())

        for object_set in pm.ls(type="objectSet"):
            if object_set.nodeType() != "objectSet":
                continue

            if not self.validate_set(object_set):
                continue

            # Exclude specific sets

            if object_set.name() in self.invalid_sets:
                continue

            # Checking instance type.
            instance_type = "remote" if object_set in remote_members else "local"

            # Add an instance per format supported.
            for fmt in ["mayaBinary", "mayaAscii", "alembic"]:
                # Remove illegal disk characters
                name = object_set.name().replace(":", "_")

                instance = context.create_instance(name=name)
                instance.add(object_set)

                instance.data.update(self.get_instance_data(object_set, fmt, instance_type))

                if not hasattr(object_set, fmt):
                    pm.addAttr(
                        object_set,
                        longName=fmt,
                        defaultValue=False,
                        attributeType="bool"
                    )
                    attr = pm.Attribute(object_set.name() + "." + fmt)
                    pm.setAttr(attr, channelBox=True)

                collection = self.generate_collection(context.data["currentFile"], fmt, name)
                instance.data["collection"] = collection

                if fmt == 'alembic':
                    remote_instance = context.create_instance(name=name)
                    remote_instance.add(object_set)

                    remote_instance.data.update(self.get_instance_data(object_set, fmt, "remote"))
                    remote_instance.data["collection"] = self.generate_collection(context.data["currentFile"], fmt, name)

