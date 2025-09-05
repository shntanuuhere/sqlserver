#!/bin/bash

# Exit on any error
set -e

# --- Install System Dependencies (Microsoft ODBC Driver) ---
# This section is specific to the Debian Linux environment Render uses.

# Update package lists
apt-get update

# Install required tools
apt-get install -y curl apt-transport-https

# Add Microsoft's official repository key
curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -

# Add the Microsoft repository for Debian 11 (which Render uses)
curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list

# Update package lists again to include the new repository
apt-get update

# Install the driver, automatically accepting the EULA
ACCEPT_EULA=Y apt-get install -y msodbcsql17

# --- Install Python Dependencies ---
# Now, install the packages from your requirements.txt file
pip install -r requirements.txt
```

#### Step 3: Update Your Build Command in Render

Now, go to your service's dashboard on Render.
1.  Go to the **Settings** tab.
2.  Find the **Build Command** field.
3.  Change it from `pip install -r requirements.txt` to this:

    ```bash
    bash build.sh
    ```



#### Step 4: Commit and Push

Save the new `build.sh` file, commit it to your repository, and push it to GitHub.
```bash
git add build.sh
git commit -m "feat: Add build script to install ODBC driver"
git push
