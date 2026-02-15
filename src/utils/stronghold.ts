/**
 * Wrapper around Tauri Stronghold for credential storage
 */

import { Client, Stronghold } from "@tauri-apps/plugin-stronghold";
import { appDataDir } from "@tauri-apps/api/path";

let strongholdClient: Client | null = null;

const VAULT_NAME = "incident-workbench-vault";
const RECORD_PATH = "credentials";

/**
 * Initialize Stronghold client
 */
async function getStrongholdClient(): Promise<Client> {
  if (strongholdClient) {
    return strongholdClient;
  }

  try {
    const appDir = await appDataDir();
    const strongholdPath = `${appDir}/credentials.stronghold`;

    const stronghold = await Stronghold.load(strongholdPath, "incident-workbench-password");
    strongholdClient = await stronghold.loadClient(VAULT_NAME);

    return strongholdClient;
  } catch (error) {
    console.error("Failed to initialize Stronghold client:", error);
    throw new Error(`Stronghold initialization failed: ${error}`);
  }
}

/**
 * Save credentials to Stronghold
 */
export async function saveCredentials(key: string, value: string): Promise<void> {
  const client = await getStrongholdClient();
  const store = client.getStore();

  const encoder = new TextEncoder();
  const encoded = encoder.encode(value);
  await store.insert(`${RECORD_PATH}/${key}`, Array.from(encoded));
}

/**
 * Read credentials from Stronghold
 */
export async function readCredentials(key: string): Promise<string | null> {
  try {
    const client = await getStrongholdClient();
    const store = client.getStore();

    const data = await store.get(`${RECORD_PATH}/${key}`);
    if (!data) {
      // Not found is expected for new keys, return null without error
      return null;
    }

    const decoder = new TextDecoder();
    try {
      return decoder.decode(data);
    } catch (decodeError) {
      console.error(`Failed to decode credential '${key}':`, decodeError);
      throw new Error(`Credential decode error for '${key}': ${decodeError}`);
    }
  } catch (error) {
    // Distinguish between "not found" (which is fine) and actual errors
    if (error instanceof Error && error.message.includes("Credential decode error")) {
      throw error;
    }
    console.error("Failed to read credentials:", error);
    return null;
  }
}

/**
 * Delete credentials from Stronghold
 */
export async function deleteCredentials(key: string): Promise<void> {
  const client = await getStrongholdClient();
  const store = client.getStore();

  await store.remove(`${RECORD_PATH}/${key}`);
}

/**
 * Save Jira credentials
 */
export async function saveJiraCredentials(
  url: string,
  email: string,
  apiToken: string
): Promise<void> {
  await saveCredentials("jira_url", url);
  await saveCredentials("jira_email", email);
  await saveCredentials("jira_api_token", apiToken);
}

/**
 * Read Jira credentials
 */
export async function readJiraCredentials(): Promise<{
  url: string;
  email: string;
  apiToken: string;
} | null> {
  const url = await readCredentials("jira_url");
  const email = await readCredentials("jira_email");
  const apiToken = await readCredentials("jira_api_token");

  if (!url || !email || !apiToken) {
    return null;
  }

  return { url, email, apiToken };
}

/**
 * Save Slack credentials
 */
export async function saveSlackCredentials(
  botToken: string,
  userToken?: string
): Promise<void> {
  await saveCredentials("slack_bot_token", botToken);
  if (userToken) {
    await saveCredentials("slack_user_token", userToken);
  }
}

/**
 * Read Slack credentials
 */
export async function readSlackCredentials(): Promise<{
  botToken: string;
  userToken?: string;
} | null> {
  const botToken = await readCredentials("slack_bot_token");
  if (!botToken) {
    return null;
  }

  const userToken = await readCredentials("slack_user_token");

  return {
    botToken,
    userToken: userToken || undefined,
  };
}
