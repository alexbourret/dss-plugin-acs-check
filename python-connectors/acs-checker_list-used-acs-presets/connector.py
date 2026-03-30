from dataiku.connector import Connector
from records_limit import RecordsLimit
import dataiku


class ACSCheckerConnector(Connector):

    def __init__(self, config, plugin_config):
        Connector.__init__(self, config, plugin_config)  # pass the parameters to the base class

    def get_read_schema(self):
        return None

    def generate_rows(self, dataset_schema=None, dataset_partitioning=None,
                      partition_id=None, records_limit=-1):
        limit = RecordsLimit(records_limit)
        client = dataiku.api_client()
        dss_client_url = client.get_general_settings().get_raw().get('studioExternalUrl', "set studioExternalUrl")
        plugin_handle = client.get_plugin("sharepoint-online")
        plugin_usages = plugin_handle.list_usages()
        if plugin_usages.usages:
            for plugin_usage in plugin_usages.usages:
                raw_params = None
                project = client.get_project(plugin_usage.project_key)
                if plugin_usage.object_type == "RECIPE":
                    recipe = project.get_recipe(plugin_usage.object_id)
                    recipe_settings = recipe.get_settings()
                    raw_params = recipe_settings.raw_params
                    item_type = "recipes"
                elif plugin_usage.object_type == "DATASET":
                    dataset = project.get_dataset(plugin_usage.object_id)
                    item_type = "datasets"
                    raw_params = None
                    try:
                        dataset_settings = dataset.get_settings()
                        raw_params = dataset_settings.get_raw_params()
                    except Exception as exception:
                        print("Dataset {} could not be retrieved".format(plugin_usage.object_id))
                        continue
                auth_type = get_auth_type(raw_params)
                output = {
                    "dss_client": dss_client_url,
                    "element_type": plugin_usage.element_type,
                    "kind": plugin_usage.element_kind,
                    "project_key": plugin_usage.project_key,
                    "object_id": plugin_usage.object_id,
                }
                if auth_type == "site-app-permissions":
                    output["Status"] = "KO"
                    if item_type == "datasets":
                        output["To check"] = "{}/projects/{}/datasets/{}/settings/".format(
                            dss_client_url,
                            plugin_usage.project_key,
                            plugin_usage.object_id
                        )
                    else:
                        output["To check"] = "{}/projects/{}/recipes/{}/".format(
                            dss_client_url,
                            plugin_usage.project_key,
                            plugin_usage.object_id
                        )
                else:
                    output["Status"] = "OK"
                    output["To check"] = None
                yield output
                if limit.is_reached():
                    return

        for project_info in client.list_projects():
            output = {}
            project_key = project_info["projectKey"]
            project = client.get_project(project_key)
            for folder_summary in project.list_managed_folders():
                folder_id = folder_summary["id"]
                folder = project.get_managed_folder(folder_id)
                definition = folder.get_definition()
                folder_type = definition.get("type", "")
                if folder_type != "fsprovider_sharepoint-online_sharepoint-online_shared-documents":
                    continue
                auth_type = get_auth_type(definition)
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
                else:
                    output["Status"] = "OK"
                    output["To check"] = None
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
    return config_section.get("auth_type", None)


def get_config_section(raw_parameters):
    if not isinstance(raw_parameters, dict):
        return {}
    if "customConfig" in raw_parameters:
        return raw_parameters.get("customConfig")
    elif "params" in raw_parameters:
        return raw_parameters.get("params", {}).get("config", {})
    else:
        return raw_parameters.get("config", {})
