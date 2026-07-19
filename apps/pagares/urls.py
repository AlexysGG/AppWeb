from rest_framework.routers import DefaultRouter
from .views import ClienteViewSet, PagareViewSet

router = DefaultRouter()
router.register("clientes", ClienteViewSet, basename="cliente")
router.register("pagares", PagareViewSet, basename="pagare")

urlpatterns = router.urls
