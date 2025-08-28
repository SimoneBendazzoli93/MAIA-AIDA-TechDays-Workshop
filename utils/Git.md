# Sign Commits with GPG
To sign your commits with GPG, you need to follow these steps:


1. **Generate a GPG Key**: If you don't have a GPG key yet, you can generate one using the following command:
   ```
   gpg --full-generate-key
   ```
   Follow the prompts to create your key.

3. **Configure Git to Use Your GPG Key**: Once you have your GPG key, you need to tell Git to use it. First, find your GPG key ID by running:
   ```
   gpg --list-secret-keys --keyid-format LONG
   ```
   Then, configure Git with your key ID:
   ```
   git config --global user.signingkey YOUR_KEY_ID
   ```

4. **Sign Your Commits**: You can now sign your commits by using the `-S` option:
   ```
   git commit -S -m "Your commit message"
   ```
   To automatically sign all commits, run:
   ```
   git config --global commit.gpgSign true
   ```

5. **Verify Signed Commits**: To verify that a commit is signed, you can use:
   ```
   git log --show-signature
   ```

6. **Upload GPG Key to GitHub**: To upload your GPG key to GitHub, follow these steps:
   - First, export your GPG public key:
     ```
     gpg --armor --export YOUR_EMAIL@example.com
     ```
   - Copy the output and go to your GitHub account settings.
   - In the "SSH and GPG keys" section, click "New GPG key", paste your key, and save it.

By following these steps, you can ensure that your commits are signed with GPG, providing an extra layer of security and authenticity.

# Set Username and Email for Git Commits
To set your username and email for Git commits, use the following commands:
```
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```
