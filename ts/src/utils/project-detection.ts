/**
 * Project context detection utilities.
 * Auto-detects project name and context from the current working directory or git repo.
 */

import { execSync } from "node:child_process";
import { basename, resolve } from "node:path";

export interface ProjectContext {
  project_name: string;
  project_path: string;
  is_git_repo: boolean;
  git_remote?: string;
}

export function detectProjectContext(cwd?: string): ProjectContext | null {
  const workingDir = resolve(cwd ?? process.cwd());

  const gitInfo = detectFromGit(workingDir);
  if (gitInfo) {
    return gitInfo;
  }

  return {
    project_name: basename(workingDir),
    project_path: workingDir,
    is_git_repo: false,
  };
}

function detectFromGit(cwd: string): ProjectContext | null {
  try {
    execSync("git rev-parse --is-inside-work-tree", {
      cwd,
      stdio: "pipe",
      timeout: 2000,
    });
  } catch {
    return null;
  }

  try {
    const repoRoot = execSync("git rev-parse --show-toplevel", {
      cwd,
      stdio: "pipe",
      timeout: 2000,
    })
      .toString()
      .trim();

    const projectPath = repoRoot;
    const projectName = basename(projectPath);

    let gitRemote: string | undefined;
    try {
      const rawRemote = execSync("git remote get-url origin", {
        cwd,
        stdio: "pipe",
        timeout: 2000,
      })
        .toString()
        .trim();
      // Strip embedded credentials from git remote URL
      gitRemote = rawRemote.replace(/^(https?:\/\/)[^@]+@/, "$1");
    } catch {
      // git remote is optional
    }

    return {
      project_name: projectName,
      project_path: projectPath,
      is_git_repo: true,
      git_remote: gitRemote,
    };
  } catch {
    return null;
  }
}

export async function getProjectFromMemories(
  _db: unknown,
  _limit = 50
): Promise<string | null> {
  return null;
}
