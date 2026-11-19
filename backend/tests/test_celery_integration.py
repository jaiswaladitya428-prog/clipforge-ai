import pytest
from app.core.celery_app import celery_app
from app.workers.tasks import ping

def test_celery_app_configuration():
    assert celery_app.main == "clipforge"
    assert "app.workers.tasks" in celery_app.conf.include
    assert celery_app.conf.task_serializer == "json"
    assert celery_app.conf.task_acks_late is True

def test_celery_ping_task():
    # Direct task execution (Week 2 verification)
    res = ping()
    assert isinstance(res, dict)
    assert res.get("status") == "success"
    assert res.get("message") == "ClipForge AI worker is running!"
