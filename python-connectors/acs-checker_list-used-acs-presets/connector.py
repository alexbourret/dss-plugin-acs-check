from dataiku.connector import Connector
from records_limit import RecordsLimit
import dataiku


class ACSCheckerConnector(Connector):

    def __init__(self, config, plugin_config):
        Connector.__init__(self, config, plugin_config)  # pass the parameters to the base class
        self.project_key = config.get("project_key", None)

    def get_read_schema(self):
        return None

    def generate_rows(self, dataset_schema=None, dataset_partitioning=None,
                      partition_id=None, records_limit=-1):
        limit = RecordsLimit(records_limit)
        client = dataiku.api_client()
        dss_client_url = client.get_general_settings().get_raw().get('studioExternalUrl', "set studioExternalUrl")

        projects_keys = []
        if not self.project_key:
            projects = client.list_projects()
            for project in projects:
                projects_keys.append(project.get("projectKey"))
        else:
            projects_keys = [self.project_key]
        for project_key in projects_keys:
            output = {}
            project = client.get_project(project_key)
            for folder_summary in project.list_managed_folders():
                folder_id = folder_summary["id"]
                folder = project.get_managed_folder(folder_id)
                definition = folder.get_definition()
                folder_type = definition.get("type", "")
                if folder_type != "fsprovider_sharepoint-online_sharepoint-online_shared-documents":
                    continue
                auth_type, preset_name = get_auth_type(definition)
                output = {
                    "dss_client": dss_client_url,
                    "element_type": folder_type,
                    "kind": "python-fs-providers",
                    "project_key": project_key,
                    "object_id": folder_id,
                }
                if auth_type == "site-app-permissions":
                    output["Status"] = "KO"
                    output["To check"] = "{}/projects/{}/managedfolder/{}/settings/".format(
                        dss_client_url,
                        project_key,
                        folder_id
                    )
                    output["Preset name"] = preset_name
                else:
                    output["Status"] = "OK"
                    output["To check"] = None
                    output["Preset name"] = None
                yield output
                if limit.is_reached():
                    return

            for dataset in project.list_datasets():
                dataset_type = dataset.get("type")
                dataset_id = dataset.get("name")
                if dataset_type == "CustomPython_sharepoint-online_lists":
                    output = {
                        "dss_client": dss_client_url,
                        "element_type": dataset_type,
                        "kind": "python-connectors",
                        "project_key": project_key,
                        "object_id": dataset_id,
                    }
                    auth_type, preset_name = get_auth_type(dataset)
                    if auth_type == "site-app-permissions":
                        output["Status"] = "KO"
                        output["To check"] = "{}/projects/{}/datasets/{}/settings/".format(
                            dss_client_url,
                            project_key,
                            dataset_id
                        )
                        output["Preset name"] = preset_name
                    else:
                        output["Status"] = "OK"
                        output["To check"] = None
                        output["Preset name"] = None
                    yield output
                    if limit.is_reached():
                        return
                if dataset_type == "fsprovider_sharepoint-online_sharepoint-online_shared-documents":
                    output = {
                        "dss_client": dss_client_url,
                        "element_type": dataset_type,
                        "kind": "python-fs-providers",
                        "project_key": project_key,
                        "object_id": dataset_id,
                    }
                    auth_type, preset_name = get_auth_type(dataset)
                    if auth_type == "site-app-permissions":
                        output["Status"] = "KO"
                        output["To check"] = "{}/projects/{}/datasets/{}/settings/".format(
                            dss_client_url,
                            project_key,
                            dataset_id
                        )
                        output["Preset name"] = preset_name
                    else:
                        output["Status"] = "OK"
                        output["To check"] = None
                        output["Preset name"] = None
                    yield output
                    if limit.is_reached():
                        return

            for recipe in project.list_recipes():
                recipe_type = recipe.get("type")
                recipe_id = recipe.get("name")
                if recipe_type == "CustomCode_sharepoint-online-append-list":
                    output = {
                        "dss_client": dss_client_url,
                        "element_type": recipe_type,
                        "kind": "custom-recipes",
                        "project_key": project_key,
                        "object_id": recipe_id,
                    }
                    auth_type, preset_name = get_auth_type(recipe)
                    if auth_type == "site-app-permissions":
                        output["Status"] = "KO"
                        output["To check"] = "{}/projects/{}/recipes/{}/".format(
                            dss_client_url,
                            project_key,
                            recipe_id
                        )
                        output["Preset name"] = preset_name
                    else:
                        output["Status"] = "OK"
                        output["To check"] = None
                        output["Preset name"] = None
                    yield output
                    if limit.is_reached():
                        return

    def get_writer(self, dataset_schema=None, dataset_partitioning=None,
                   partition_id=None, write_mode="OVERWRITE"):
        raise NotImplementedError

    def get_partitioning(self):
        raise NotImplementedError

    def list_partitions(self, partitioning):
        return []

    def partition_exists(self, partitioning, partition_id):
        raise NotImplementedError

    def get_records_count(self, partitioning=None, partition_id=None):
        raise NotImplementedError


def get_auth_type(raw_parameters):
    config_section = get_config_section(raw_parameters)
    preset_name = get_preset_name(config_section)
    return config_section.get("auth_type", None), preset_name


def get_config_section(raw_parameters):
    if not isinstance(raw_parameters, dict):
        return {}
    if "customConfig" in raw_parameters:
        return raw_parameters.get("customConfig")
    elif "params" in raw_parameters:
        params = raw_parameters.get("params", {})
        if "customConfig" in params:
            return params.get("customConfig")
        else:
            return params.get("config")
    else:
        return raw_parameters.get("config", {})


def get_preset_name(raw_parameters):
    auth_type = raw_parameters.get("auth_type")
    preset = get_preset(raw_parameters, auth_type)
    mode = preset.get("mode")
    if mode == "INLINE":
        return "Manually defined"
    elif mode == "NONE":
        return "None"
    elif mode == "PRESET":
        return preset.get("name")


def get_preset(raw_paremeters, auth_type):
    if auth_type == "site-app-permissions":
        return raw_paremeters.get("site_app_permissions", {})
    return {}
