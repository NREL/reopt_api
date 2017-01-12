# config valid only for current version of Capistrano
lock "3.7.1"

set :application, "reopt_api"
set :repo_url, "git@github.nrel.gov:ndiorio/reopt_api.git"

# Set the base deployment directory.
set :deploy_to_base, "/srv/data/apps"

# Set the user the web app runs as.
set :foreman_user, "www-data-local"
set :file_permissions_users, ["www-data-local"]

# Don't replace github.nrel.gov references for internal servers.
set :bundle_swap_nrel_git_references, false

# Symlink other directories across deploys.
set :linked_dirs, fetch(:linked_dirs, []).push("tmp")

namespace :app do
  task :pip_install do
    on roles(:app) do
      within release_path do
        execute "virtualenv", "env"
        execute "./env/bin/pip", "install", "-r", "requirements.txt"
      end
    end
  end

  task :keys do
    on roles(:app) do
      execute "ln", "-snf", "/etc/reopt-api-secrets/keys.py", "#{release_path}/keys.py"
    end
  end

  before "deploy:updated", "app:pip_install"
  before "deploy:updated", "app:keys"
end
