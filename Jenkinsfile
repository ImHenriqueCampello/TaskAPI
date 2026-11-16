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
    }

    environment {
        REPORT_DIR = 'reports'
        TEST_DATABASE_URL = credentials('taskapi-test-database-url')
    }

    stages {
        stage('Checkout') {
            steps {
                script {
                    def scmVars = checkout scm
                    env.CHECKED_OUT_BRANCH = scmVars.GIT_BRANCH ?: env.GIT_BRANCH ?: ''
                }
                sh 'rm -rf reports && mkdir -p reports'
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
                sh '.venv/bin/python -m compileall -q app'
            }
        }
        stage('Test') {
            steps {
                sh '''
                    set -eu
                    .venv/bin/python -m pytest -v --junitxml="$REPORT_DIR/junit.xml" \
                      --cov=app --cov-report=term-missing \
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
                    sh '''
                        set -eu
                        set +x
                        docker_config="$(mktemp -d)"
                        trap 'docker --config "$docker_config" logout >/dev/null 2>&1 || true; rm -rf "$docker_config"' EXIT
                        export DOCKER_CONFIG="$docker_config"
                        printf '%s' "$DOCKERHUB_TOKEN" | docker login --username "$DOCKERHUB_USERNAME" --password-stdin
                        docker tag "taskapi:${BUILD_NUMBER}-${SHORT_COMMIT}" joaolucenalima/taskapi:latest
                        docker push joaolucenalima/taskapi:latest
                    '''
                }
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: 'reports/**', allowEmptyArchive: true, fingerprint: true
            cleanWs()
        }
    }
}
