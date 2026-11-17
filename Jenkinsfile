pipeline {
    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
        timeout(time: 30, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '20'))
    }

    triggers {
        githubPush()
        pollSCM('H/5 * * * *')
    }

    environment {
        PUBLICATION_STATUS = 'not-run'
        REPORT_DIR = 'reports'
        DIST_DIR = 'dist'
        // TEST_DATABASE_URL, NOTIFY_EMAIL, SMTP_* e DOCKERHUB_REPO vêm das variáveis de
        // ambiente do container Jenkins (docker-compose.yml + .env), nunca fixas aqui.
    }

    stages {
        stage('Checkout') {
            steps {
                script {
                    def scmVars = checkout scm
                    env.SHORT_COMMIT = sh(script: 'git rev-parse --short=12 HEAD', returnStdout: true).trim()
                    env.CHECKED_OUT_BRANCH = scmVars.GIT_BRANCH ?: env.GIT_BRANCH ?: ''
                }
                sh 'rm -rf reports dist && mkdir -p reports dist'
            }
        }
        stage('Install') {
            steps {
                sh '''
                    set -eu
                    python3 -m venv .venv
                    .venv/bin/python -m pip install --upgrade pip
                    .venv/bin/python -m pip install -r requirements.txt
                '''
            }
        }
        stage('Validate') {
            steps {
                sh '.venv/bin/python -m compileall -q app scripts'
            }
        }
        stage('Test') {
            steps {
                sh '''
                    set -eu
                    .venv/bin/python -m pytest -v --junitxml="$REPORT_DIR/junit.xml" \
                      --cov=app --cov=scripts --cov-report=term-missing \
                      --cov-report=xml:"$REPORT_DIR/coverage.xml" \
                      --cov-report=html:"$REPORT_DIR/html" --cov-fail-under=90
                '''
            }
            post {
                always {
                    junit testResults: 'reports/junit.xml', allowEmptyResults: true
                    publishHTML(target: [
                        allowMissing: true,
                        alwaysLinkToLastBuild: true,
                        keepAll: true,
                        reportDir: 'reports/html',
                        reportFiles: 'index.html',
                        reportName: 'Coverage Report'
                    ])
                }
            }
        }
        stage('Build') {
            steps {
                script {
                    env.SHORT_COMMIT = sh(script: 'git rev-parse --short=12 HEAD', returnStdout: true).trim()
                }
                sh 'docker build --target runtime -t taskapi:${BUILD_NUMBER}-${SHORT_COMMIT} .'
                // Pacote da aplicação (artefato): código + dependências + Dockerfile
                sh 'tar czf "$DIST_DIR/taskapi-${BUILD_NUMBER}-${SHORT_COMMIT}.tar.gz" app requirements.txt Dockerfile'
            }
        }
        stage('Publish Docker Hub') {
            when {
                expression {
                    def branch = (env.BRANCH_NAME ?: env.CHECKED_OUT_BRANCH ?: '').trim()
                    return !env.CHANGE_ID && (branch == 'main' || branch == 'origin/main')
                }
            }
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'dockerhub-credentials',
                    usernameVariable: 'DOCKERHUB_USERNAME',
                    passwordVariable: 'DOCKERHUB_TOKEN'
                )]) {
                    script { env.PUBLICATION_STATUS = 'failed' }
                    sh '''
                        set -eu
                        set +x
                        docker_config="$(mktemp -d)"
                        trap 'docker --config "$docker_config" logout >/dev/null 2>&1 || true; rm -rf "$docker_config"' EXIT
                        export DOCKER_CONFIG="$docker_config"
                        repo="${DOCKERHUB_REPO:-joaolucenalima/taskapi}"
                        printf '%s' "$DOCKERHUB_TOKEN" | docker login --username "$DOCKERHUB_USERNAME" --password-stdin
                        docker tag "taskapi:${BUILD_NUMBER}-${SHORT_COMMIT}" "$repo:latest"
                        docker tag "taskapi:${BUILD_NUMBER}-${SHORT_COMMIT}" "$repo:${BUILD_NUMBER}-${SHORT_COMMIT}"
                        docker push "$repo:latest"
                        docker push "$repo:${BUILD_NUMBER}-${SHORT_COMMIT}"
                    '''
                    script { env.PUBLICATION_STATUS = 'published' }
                }
            }
        }
    }

    post {
        always {
            // Pacote (dist/) e relatórios de teste (reports/) ficam como artefatos do build
            archiveArtifacts artifacts: 'reports/**, dist/**', allowEmptyArchive: true, fingerprint: true
            script {
                // Etapa de notificação: roda mesmo quando o pipeline falha.
                // O destinatário vem da variável de ambiente NOTIFY_EMAIL (não é hardcoded).
                stage('Notificação por e-mail') {
                    try {
                        def buildUrl = env.BUILD_URL ?: ''
                        if (!buildUrl && env.JENKINS_PUBLIC_URL) {
                            def jobPath = env.JOB_NAME.split('/').collect {
                                'job/' + java.net.URLEncoder.encode(it, 'UTF-8').replace('+', '%20')
                            }.join('/')
                            buildUrl = env.JENKINS_PUBLIC_URL.replaceAll('/+$', '') + "/${jobPath}/${env.BUILD_NUMBER}/"
                        }
                        withEnv([
                            "NOTIFY_STATUS=${currentBuild.currentResult}",
                            "NOTIFY_URL=${buildUrl}",
                            "NOTIFY_DURATION=${(currentBuild.duration / 1000) as long}"
                        ]) {
                            sh '''
                                python3 scripts/notify_email.py \
                                  --status "$NOTIFY_STATUS" --job "$JOB_NAME" --build "$BUILD_NUMBER" \
                                  --url "$NOTIFY_URL" --commit "${SHORT_COMMIT:-n/a}" \
                                  --branch "${CHECKED_OUT_BRANCH:-n/a}" --duration-seconds "$NOTIFY_DURATION" \
                                  --docker-repo "$DOCKERHUB_REPO" --publication-status "$PUBLICATION_STATUS"
                            '''
                        }
                    } catch (err) {
                        // Falha no envio não deve reprovar o build
                        echo "Não foi possível enviar o e-mail: ${err}"
                    }
                }
            }
        }
        cleanup {
            cleanWs()
        }
    }
}
