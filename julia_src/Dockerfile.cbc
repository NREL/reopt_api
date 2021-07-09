FROM julia:1.6.1

# Install Julia packages
ENV JULIA_NUM_THREADS=2

WORKDIR /opt/julia_src
COPY reopt_model.jl .
COPY utils.jl .

WORKDIR /opt/julia_src/cbc
COPY cbc/ .
RUN julia --project=/opt/julia_src/cbc -e 'import Pkg; Pkg.instantiate();'
RUN julia --project=/opt/julia_src/cbc precompile.jl
EXPOSE 8081

CMD ["bash"]