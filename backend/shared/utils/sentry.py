import logging

from shared.config.settings import settings

logger = logging.getLogger("parksight.sentry")


def init_sentry(service_name: str):
    dsn = settings.SENTRY_DSN
    if not dsn:
        logger.info("SENTRY_DSN not set — skipping Sentry init for %s", service_name)
        return
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

        sentry_sdk.init(
            dsn=dsn,
            service_name=service_name,
            traces_sample_rate=0.2,
            profiles_sample_rate=0.1,
            integrations=[
                FastApiIntegration(),
                SqlalchemyIntegration(),
            ],
        )
        logger.info("Sentry initialized for %s", service_name)
    except ImportError:
        logger.warning("sentry_sdk not installed — skipping Sentry")
    except Exception:
        logger.exception("Failed to initialize Sentry for %s", service_name)
