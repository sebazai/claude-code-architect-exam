FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    openssh-client \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js (required for Claude Code CLI)
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install Claude Code CLI globally
RUN npm install -g @anthropic-ai/claude-code

# Create a non-root user
RUN useradd -m -s /bin/bash examuser
USER examuser
WORKDIR /workspace

# Install the exam app in editable mode as the non-root user
COPY --chown=examuser:examuser exam-app/ /workspace/exam-app/
RUN pip install --user -e /workspace/exam-app/
