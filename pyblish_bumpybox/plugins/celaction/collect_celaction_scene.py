import pyblish.api


class CollectCelActionScene(pyblish.api.ContextPlugin):
    """ Converts the path flag value to the current file in the context. """

    order = pyblish.api.CollectorOrder

    def process(self, context):

        context.data["currentFile"] = context.data("kwargs")["path"][0]
