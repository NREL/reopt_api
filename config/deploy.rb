# config valid only for current version of Capistrano
lock "~> 3.12.0"

set :application, "reopt_api"
set :repo_url, "https://github.com/NREL/REopt_Lite_API.git"

# Set the base deployment directory.
set :deploy_to_base, "/srv/data/apps"

# Set the user the web app runs as.
set :foreman_user, "www-data-local"
set :file_permissions_users, ["www-data-local"]

# Symlink other directories across deploys.
set :linked_dirs, fetch(:linked_dirs, []).push("static/files", "tmp")

# Allow the web user to write files for Xpress
set :file_permissions_paths, fetch(:file_permissions_paths, []).push("static/files")

namespace :app do
  task :pip_install do
    on roles(:app) do
      within release_path do
        execute "rm", "-rf", "env"
        execute "virtualenv", "env", "--python=/bin/python3"
        execute "./env/bin/pip3", "install", "-r", "requirements.txt"
        execute "julia", "--project='./julia_envs/Xpress/'", "-e", "'import Pkg; Pkg.instantiate();'"
        execute "julia", "--project='./julia_envs/Xpress/'", "./julia_envs/Xpress/precompile.jl"
        execute "julia", "--project='./julia_envs/Xpress/'", "-e", "'ENV[\"PYTHON\"] = \"./env/bin/python3\"; import Pkg; Pkg.build(\"PyCall\")'"
        execute "./env/bin/python", "-c", "'import julia; julia.install()'"
      end
    end
  end

  task :keys do
    on roles(:app) do
      execute "ln", "-snf", "/etc/reopt-api-secrets/keys.py", "#{release_path}/keys.py"
    end
  end

  task :migrate do
    on roles(:db) do
      within release_path do
        with "PATH" => "#{release_path}/env/bin:$PATH", "VIRTUAL_ENV" => "#{release_path}/env", "DJANGO_SETTINGS_MODULE" => fetch(:django_settings_module) do
          execute "./env/bin/python", "manage.py", "migrate", "--noinput"
          execute "./env/bin/python", "manage.py", "collectstatic", "--noinput"
        end
      end
    end
  end

  before "deploy:updated", "app:pip_install"
  before "deploy:updated", "app:keys"
  after "deploy:updated", "app:migrate"
end
