pipeline{
    agent any
    triggers {
        pollSCM('H/15 * * * *')
    }
    environment {
        DIND_ALIAS = 'docker'
        DEPLOY_PORT = '9090'
        IMAGE_NAME = 'os-image-repo'
        FLASK_CONTAINER = 'flask-os-image-repo'
        NGINX_CONTAINER = 'nginx-os-image-repo'
    }
    stages{
        stage('Unit tests'){
            steps{
                sh 'docker build -t $IMAGE_NAME .'
                sh 'docker run --rm $IMAGE_NAME /bin/sh -c "python -m unittest discover -v -p \'unit_tests\' || exit 1"'
                sh 'docker run --rm $IMAGE_NAME /bin/sh -c "pip install -q -r test_requirements.txt && flake8 || exit 1"'
                sh 'docker image rm $IMAGE_NAME'
            }
        }
        stage('Integration tests'){
            steps{
                script{
                    // Make sure python venv is created
                    def envDir = './env'
                    if (!fileExists(envDir)) {
                        sh "python3 -m venv ${envDir}"
                    }

                    // Make sure volumes directories exist
                    def dataDir = './data'
                    if (!fileExists(dataDir)) {
                        sh "mkdir ${dataDir}"
                    }
                    

                    def nginxLogsDir = './nginx/logs'
                    if (!fileExists(nginxLogsDir)) {
                        sh "mkdir ${nginxLogsDir}"
                    }
                }
                sh './env/bin/pip install -q -r integration_tests/requirements.txt'
                sh 'docker compose up -d --build'
                sh 'env/bin/python -m integration_tests.integration_tests --url "http://$DIND_ALIAS:$DEPLOY_PORT/"'
                
                // Cleaning data
                sh 'docker exec $FLASK_CONTAINER /bin/sh -c "rm -rf /data/*"'
                sh 'docker exec $NGINX_CONTAINER /bin/sh -c "rm -rf /var/log/nginx/logs/*"'
                sh 'docker compose down --rmi all --volumes --remove-orphans'
            }
        }
    }
}