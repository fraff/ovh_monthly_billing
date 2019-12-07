#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {
    "metadata_version": "1.1",
    "status": ["preview"],
    "supported_by": "community",
}

DOCUMENTATION = '''
---
module: ovh_monthly_billing
author: Francois Lallart (@fraff)
version_added: "2.10"
short_description: Manage OVH monthly billing
description:
    - Enable monthly billing on OVH cloud intances
requirements: [ "ovh" ]
options:
    project_id:
        required: true
        type: str
        description:
            - ID of the project, get it with https://api.ovh.com/console/#/cloud/project#GET
    instance_id:
        required: true
        type: str
        description:
            - ID of the instance, get it with https://api.ovh.com/console/#/cloud/project/%7BserviceName%7D/instance#GET
    state:
        required: false
        type: str
        default: present
        choices: ['present', 'absent']
        description:
            - useless I guess
'''

EXAMPLES = '''
# basic
  - ovh_monthly_billing: project_id=0c727a20aa144485b70c44dee9123b46 instance_id=8fa89ad2-8f08-4220-9fa4-9695ea23e948

# more complex
  - os_server_facts:
      cloud: myProjectName
      region_name: myRegionName
      server: myServerName
    # force run even in check_mode
    check_mode: no

  - name: ovh_monthly_billing
    ovh_monthly_billing:
      project_id: "{{ openstack_servers.0.tenant_id }}"
      instance_id: "{{ openstack_servers.0.id }}"
'''

RETURN = '''
'''

import os
import sys

try:
    import ovh
    import ovh.exceptions
    from ovh.exceptions import APIError
    HAS_OVH = True
except ImportError:
    HAS_OVH = False

from ansible.module_utils.basic import AnsibleModule


def main():
    module = AnsibleModule(
        argument_spec=dict(
            project_id=dict(required=True),
            instance_id=dict(required=True),
            state=dict(default='present', choices=['present', 'absent']),
        ),
        supports_check_mode=True
    )

    # Get parameters
    project_id = module.params.get('project_id')
    instance_id = module.params.get('instance_id')
    state = module.params.get('state')
    project = ""
    instance = ""
    result = ""

    # Connect to OVH API
    client = ovh.Client()

    if not HAS_OVH:
        module.fail_json(msg='python-ovh is required to run this module, see https://github.com/ovh/python-ovh')

    if state == "absent":
        module.fail_json(msg="OVH API does not allow to remove monthly billing")

    # Check that the instance exists
    try:
        project = client.get('/cloud/project/{0}'.format(project_id))
    except ovh.exceptions.ResourceNotFoundError:
        module.fail_json(msg='project {0} does not exist'.format(project_id))

    # Check that the instance exists
    try:
        instance = client.get('/cloud/project/{0}/instance/{1}'.format(project_id, instance_id))
    except ovh.exceptions.ResourceNotFoundError:
        module.fail_json(msg='instance {0} does not exist in project {1}'.format(instance_id, project_id))

    # Is monthlyBilling already enabled or pending ?
    if instance['monthlyBilling'] is not None:
        if instance['monthlyBilling']['status'] in ['ok', 'activationPending']:
            module.exit_json(changed=False, result=instance['monthlyBilling'])

    if module.check_mode:
        module.exit_json(changed=True, msg="Dry Run!")

    else:
        try:
            result = client.post('/cloud/project/{0}/instance/{1}/activeMonthlyBilling'.format(project_id, instance_id))
            module.exit_json(changed=True, result=result['monthlyBilling'])
        except APIError as apiError:
            module.fail_json(changed=False, msg="Failed to call OVH API: {0}".format(apiError))

    # We should never reach here
    module.fail_json(msg='Internal ovh_monthly_billing module error')


if __name__ == "__main__":
    main()
