FROM python:3.12-slim-bookworm AS runtime
ENV PYTHONNOUSERSITE=1 PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 XDG_CACHE_HOME=/opt/caldova-cache
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates curl gnupg unixodbc libgssapi-krb5-2 \
    && curl -fsSLo /tmp/packages-microsoft-prod.deb https://packages.microsoft.com/config/debian/12/packages-microsoft-prod.deb \
    && dpkg -i /tmp/packages-microsoft-prod.deb \
    && apt-get update && ACCEPT_EULA=Y apt-get install -y --no-install-recommends msodbcsql18 \
    && rm -rf /var/lib/apt/lists/* /tmp/packages-microsoft-prod.deb
WORKDIR /app
COPY requirements.lock.txt ./
RUN pip install --no-cache-dir -r requirements.lock.txt && pip check \
    && python -m copilot download-runtime
COPY runtime ./runtime
RUN useradd --create-home --uid 10001 learner && chown -R learner:learner /app
USER learner
EXPOSE 8088
CMD ["python", "-m", "runtime.server"]

FROM runtime AS fixture
USER root
COPY Labfiles/04-caldova-agents/Python/qualification-tool/capacity_tool.py Labfiles/04-caldova-agents/Python/qualification-tool/qualification.py Labfiles/04-caldova-agents/Python/qualification-tool/policy.py Labfiles/04-caldova-agents/Python/qualification-tool/gxp_checks.py /app/Labfiles/04-caldova-agents/Python/qualification-tool/
COPY Labfiles/04-caldova-agents/data /app/Labfiles/04-caldova-agents/data
RUN chown -R learner:learner /app/Labfiles
USER learner

FROM runtime AS core
# Deliberately excludes CSVs, fixture data, qualifications, solution and local config.
