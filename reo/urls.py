# *********************************************************************************
# REopt, Copyright (c) 2019-2020, Alliance for Sustainable Energy, LLC.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
# Redistributions of source code must retain the above copyright notice, this list
# of conditions and the following disclaimer.
#
# Redistributions in binary form must reproduce the above copyright notice, this
# list of conditions and the following disclaimer in the documentation and/or other
# materials provided with the distribution.
#
# Neither the name of the copyright holder nor the names of its contributors may be
# used to endorse or promote products derived from this software without specific
# prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT,
# INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
# OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
# OF THE POSSIBILITY OF SUCH DAMAGE.
# *********************************************************************************
from . import views
from django.conf.urls.static import static
from django.conf import settings
from django.urls import re_path

urlpatterns = [
    re_path(r'^annual_kwh/?$', views.annual_kwh),
    re_path(r'^invalid_urdb/?$', views.invalid_urdb),
    re_path(r'^help/?$', views.help),
    re_path(r'^job/(?P<run_uuid>[0-9a-f-]+)/results/?$', views.results),
    re_path(r'^simulated_load/?$', views.simulated_load),
    re_path(r'^emissions_profile/?$', views.emissions_profile),
    re_path('^generator_efficiency/?$', views.generator_efficiency),
    re_path(r'^chp_defaults/?$', views.chp_defaults),
    re_path(r'^loadprofile_chillerthermal_chiller_cop/?$', views.loadprofile_chillerthermal_chiller_cop),
    re_path(r'^absorption_chiller_defaults/?$', views.absorption_chiller_defaults),
    re_path(r'^schedule_stats/?$', views.schedule_stats),
    re_path(r'^ground_conductivity/?$', views.ground_conductivity),
    re_path(r'^job/(?P<run_uuid>[0-9a-f-]+)/remove/?$', views.remove),
]+ static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
