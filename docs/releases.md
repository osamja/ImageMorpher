# Drafting a new Imagemorpher

Creating a release branch and tagging the corresponding Docker image with the release version is a good practice for versioning releases with Git and Docker images. This allows you to manage different versions of your application and easily switch between them as needed. Here's a step-by-step guide to implementing this workflow:

Create a release branch: From the master branch, create a new release branch with a name that reflects the release version (e.g., release/v1.0.0).

```
git checkout master
git pull
git checkout -b release/v1.0.0
```

Update version information: Update any version information in your application, such as version numbers in package.json, setup.py, or any other relevant files. Commit these changes to the release branch.

```
git add .
git commit -m "Update version to v1.0.0"
```
   
Push the release branch: Push the release branch to the remote repository.

```
git push origin release/v1.0.0
```
Create a Git tag: Create a Git tag for the release. This provides a reference point in your Git history that corresponds to the release version.


```
git tag v1.0.0
git push origin v1.0.0
```

Build the Docker image: Build the Docker image for the release and tag it with the release version. Make sure you're on the release branch (release/v1.0.0) when building the image.

```
docker build -t your-dockerhub-username/your-image-name:v1.0.0 .
```

Push the Docker image: Push the tagged Docker image to the Docker registry.

```
docker push your-dockerhub-username/your-image-name:v1.0.0
```

Merge the release branch: If necessary, merge the release branch back into the master branch or any other branches where the changes should be applied.

By following these steps, you can maintain a clear release history in both your Git repository and Docker registry, making it easy to track and manage different versions of your application.