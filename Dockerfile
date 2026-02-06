cat > ~/SupersetLLM/Dockerfile << 'EOF'
FROM apache/superset:latest

USER root

# Installiere PostgreSQL-Treiber
RUN pip install psycopg2-binary

USER superset

EXPOSE 8088
EOF
