"""Celery configuration."""
task_serializer = 'json'
result_serializer = 'json'
accept_content = ['json']
timezone = 'UTC'
enable_utc = True
task_track_started = True
task_time_limit = 600
task_soft_time_limit = 540
worker_max_tasks_per_child = 50
worker_prefetch_multiplier = 1
task_acks_late = True

beat_schedule = {
    'cleanup-stale-tasks': {
        'task': 'celery_app.tasks.cleanup_stale_tasks',
        'schedule': 300.0,
    },
    'refresh-model-cache': {
        'task': 'celery_app.tasks.refresh_model_cache',
        'schedule': 600.0,
    },
}
