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
                checkout scm
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
    }

    post {
        always {
            archiveArtifacts artifacts: 'reports/**', allowEmptyArchive: true, fingerprint: true
            cleanWs()
        }
    }
}
