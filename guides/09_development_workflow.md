# 9. Development Workflow

This guide outlines the recommended development workflow for contributing to the ShoppingLists project. Following these guidelines will help maintain code quality, ensure consistency, and keep documentation in sync with the application.

## 1. Getting Started

1.  **Ensure Setup is Complete:** Before starting any new work, make sure you have followed the [Setup and Installation Guide](./01_setup_and_installation.md) and your local environment is working correctly.
2.  **Understand the Task:** Clearly understand the requirements of the feature or bug you are working on. Refer to the project's issue tracker or task management system.
3.  **Pull Latest Changes:** Always start by pulling the latest changes from the main development branch (e.g., `main` or `develop`) to avoid conflicts and ensure you're working with the most up-to-date codebase:
    ```bash
    git checkout main  # Or your primary development branch
    git pull origin main
    ```

## 2. Branching Strategy

*   **Feature Branches:** Create a new branch for every new feature, bug fix, or distinct piece of work. Branch off from the main development branch.
*   **Naming Convention:** Use a clear and descriptive branch name. A common convention is:
    *   `feature/<feature-name>` (e.g., `feature/user-profile-page`)
    *   `bugfix/<bug-description>` (e.g., `bugfix/login-error-handling`)
    *   `chore/<task-description>` (e.g., `chore/update-dependencies`)

    Example:
    ```bash
    git checkout -b feature/add-item-quantity
    ```

## 3. Development Process

1.  **Write Code:** Implement the required changes.
2.  **Follow Coding Standards:** Adhere to Python (PEP 8) and Flask best practices. Ensure your code is clean, readable, and well-commented where necessary.
3.  **Write Tests:** For new features or bug fixes that alter logic, write corresponding unit or integration tests. Refer to the [Testing Strategy Guide](./08_testing_strategy.md).
4.  **Run Tests Locally:** Ensure all tests pass before committing your changes:
    ```bash
    pytest
    ```
5.  **Commit Changes:** Make small, logical commits with clear and concise commit messages. A good commit message typically includes a short summary line and an optional more detailed body.
    ```bash
    git add .
    git commit -m "feat: Add quantity field to ListItem model and form"
    ```
    (Consider using [Conventional Commits](https://www.conventionalcommits.org/) for standardized messages.)

## 4. Documentation: Keeping it Current

**Documentation is a critical part of our development process.** Outdated documentation can be more misleading than no documentation at all.

1.  **Identify Affected Guides:** As you develop, identify which developer guides (in the `/guides` directory) are impacted by your changes. This could include:
    *   Core feature changes -> `03_core_features.md`
    *   Database model changes -> `04_database_guide.md`
    *   API endpoint changes -> (Potentially a new API guide or updates to core features/architecture)
    *   Frontend changes -> `05_frontend_development.md`
    *   Deployment process changes -> `06_deployment_guide.md`
    *   New dependencies or setup steps -> `01_setup_and_installation.md`
2.  **Update Documentation Concurrently:** Update the relevant markdown files *as you make your code changes* or immediately after. Don't leave it as an afterthought.
3.  **Clarity and Accuracy:** Ensure your documentation updates are clear, accurate, and provide enough context for another developer to understand the changes.
4.  **Part of Definition of Done:** A feature or bug fix is not considered complete until the corresponding documentation has been updated and reviewed.

## 5. Pull Requests (PRs)

1.  **Push Your Branch:** Once your work (including tests and documentation updates) is complete and committed locally, push your branch to the remote repository:
    ```bash
    git push origin feature/add-item-quantity
    ```
2.  **Create a Pull Request:** Open a Pull Request (PR) on the project's hosting platform (e.g., GitHub, GitLab) to merge your feature branch into the main development branch.
3.  **PR Description:** Write a clear PR description:
    *   Summarize the changes made.
    *   Link to any relevant issues or tasks.
    *   **Explicitly state which documentation guides were updated or confirm that no updates were necessary.**
    *   Include steps for testing or screenshots if helpful.

    **Example PR Template Snippet:**
    ```markdown
    ### Summary of Changes
    ...

    ### Related Issues
    - Fixes #123

    ### Documentation Updates
    - [x] Updated `03_core_features.md` to include item quantity.
    - [x] Updated `04_database_guide.md` with new `quantity` field in `ListItem`.
    (or [x] No documentation updates required for this change.)
    ```
4.  **Code Review:** Request a review from at least one other team member. Reviewers should check:
    *   Code correctness and quality.
    *   Test coverage and passing tests.
    *   **Accuracy and completeness of documentation updates.**
5.  **Address Feedback:** Make any necessary changes based on review feedback, commit, and push again.
6.  **Merge PR:** Once the PR is approved and all checks pass, it can be merged into the main development branch (often done by the PR author or a maintainer).

## 6. Post-Merge

*   **Delete Feature Branch:** After your PR is merged, delete your local and remote feature branches to keep the repository clean:
    ```bash
    git checkout main
    git branch -d feature/add-item-quantity
    git push origin --delete feature/add-item-quantity
    ```

By following this workflow, we aim to maintain a high-quality, well-documented, and collaborative development environment for the ShoppingLists project.
