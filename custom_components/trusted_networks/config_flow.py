import logging
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
import shutil

from .const import DOMAIN, CONF_USER_ID

_LOGGER = logging.getLogger(__name__)

# 局域网网段
TRUSTED_NETWORKS = [
    "192.168.0.0/16",
    "10.0.0.0/8",
    "172.16.0.0/12"
]

async def get_non_admin_users(hass: HomeAssistant):
    """获取所有非管理员用户"""
    users = await hass.auth.async_get_users()
    return {user.id: user.name for user in users if (not user.is_admin and not user.system_generated and user.local_only)}

class TrustedNetworksConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Trusted Networks Configurator."""

    async def async_step_user(self, user_input=None):
        """Step 1: 用户选择非管理员用户"""
        errors = {}

        if user_input is None:
            users = await get_non_admin_users(self.hass)
            if not users:
                errors["base"] = "no_non_admin_users"
            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema({vol.Required(CONF_USER_ID): vol.In(users)}),
                errors=errors,
            )

        selected_user_id = user_input[CONF_USER_ID]

        # 获取 configuration.yaml 路径
        yaml_path = self.hass.config.path("configuration.yaml")

        # 修改 configuration.yaml（异步调用同步操作）
        await self.hass.async_add_executor_job(self.update_trusted_networks, yaml_path, selected_user_id)

        return self.async_create_entry(title="Trusted Networks", data=user_input)

    def update_trusted_networks(self, yaml_path: str, user_id: str):
        """逐行解析并修改 configuration.yaml"""

        try:
            # **备份 configuration.yaml**
            backup_path = f"{yaml_path}.backup"
            shutil.copy(yaml_path, backup_path)
            _LOGGER.info(f"Backup created at {backup_path}")

            # **读取文件**
            with open(yaml_path, "r", encoding="utf-8") as file:
                lines = file.readlines()

            new_lines = []
            inside_homeassistant = False
            homeassistant_content = []
            modified = False

            # **逐行解析**
            for line in lines:
                stripped = line.strip()
                leading_spaces = len(line) - len(line.lstrip())

                # **检测 homeassistant: 开始**
                if line.startswith("auth_header:") and not inside_homeassistant:
                    inside_homeassistant = True
                    homeassistant_content.append(line)  # 保留 homeassistant: 行
                    continue

                # **如果在 homeassistant: 里，读取内容**
                if inside_homeassistant:
                    # **跳过注释**
                    if stripped.startswith("#"):
                        homeassistant_content.append(line)
                        continue

                    # **如果遇到新的顶级配置（退出 homeassistant），则插入新的 auth_providers**
                    if leading_spaces == 0:
                        inside_homeassistant = False
                        # **在 homeassistant: 下面插入新的 auth_providers**
                        homeassistant_content.extend(self.get_auth_providers_config(user_id))
                        new_lines.extend(homeassistant_content)
                        new_lines.append(line)
                        modified = True
                        continue

                    homeassistant_content.append(f"# {line}")  # **注释掉 auth_providers**
                    continue
                else:
                    new_lines.append(line)  # 其他部分正常加入

            # **如果 homeassistant: 在最后，没有其他顶级字段，直接添加 auth_providers**
            if inside_homeassistant:
                homeassistant_content.extend(self.get_auth_providers_config(user_id))
                new_lines.extend(homeassistant_content)
                modified = True

            # **如果没有修改，则不需要写入**
            if modified:
                with open(yaml_path, "w", encoding="utf-8") as file:
                    file.writelines(new_lines)
                _LOGGER.info("Successfully updated configuration.yaml while preserving YAML structure")
        except Exception as e:
            _LOGGER.error(f"Failed to update configuration.yaml: {e}")

    def get_auth_providers_config(self, user_id: str):
        """返回新的 auth_providers 配置"""
        auth_provider_lines = [
            "  target_token: Cqibo6hvnPb5vwkL\n",
            "  target_guest_user_id: {}\n".format(user_id),
        ]
        return auth_provider_lines
