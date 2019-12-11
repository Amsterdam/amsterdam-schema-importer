import functools

from .core.api import API, RequestContext, EventRequest

from .service import DatasetService, CreateDataset


class DatasetRequestContext(RequestContext):
    @property
    def service(self) -> DatasetService:
        """ Allow interfacing with application layer """
        return DatasetService()


class CreateDatasetRequest(EventRequest):
    event_cls = CreateDataset


api = API("import", context_cls=DatasetRequestContext)


@api.route("/datasets", methods=['POST'])
def create_import(context, request: CreateDatasetRequest):
    """ Create a new dataset from given JSON """
    return context.service.handle_create_dataset(request.obj)
