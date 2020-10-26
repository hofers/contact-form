# push everything to google cloud repo before deploying
git push --all google
gcloud functions deploy contact-form --allow-unauthenticated --entry-point=contact --runtime=python38 --trigger-http