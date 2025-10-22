#!/usr/bin/env python3
"""
G.H.O.S.T. v1 - Guardian, Host, and Operational Scribe Tool
A LangChain-powered agent for maintaining batserver documentation.
"""

import os
import re
from pathlib import Path
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, SystemMessage
import subprocess
import logging
import json

# logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
config_dir = os.getenv("SERVER_DIR")

def read_file_content(filepath: str) -> str:
    """Read and return the content of a file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: File not found - {filepath}")
        return ""
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return ""

def write_file_content(filepath: str, content: str) -> bool:
    """Write content to a file."""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"Error writing to {filepath}: {e}")
        return False

def edit_file_content(filepath: str, old_text: str, new_text: str, encoding: str = "utf-8") -> bool:
    file_path = Path(filepath)
    if not file_path.exists():
        print(f"Error: File not found - {file_path}")
        return False
    try:
        content = file_path.read_text(encoding=encoding)
        if old_text not in content:
            print(f"Error: Text not found - {old_text}")
            return False
        updated_content = content.replace(old_text, new_text)
        file_path.write_text(updated_content, encoding=encoding)
        return True
    except Exception as e:
        print(f"Error editing {filepath}: {e}")
        return False

def edit_file_multiple(
    filepath: str,
    json: dict,
    encoding: str = "utf-8",
) -> bool:
    file_path = Path(filepath)
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return False
    try:
        # READ ONCE
        content = file_path.read_text(encoding=encoding)    

        for edit in json["edits"]:
            if edit["old"] not in content:
                logger.error(f"Text not found: {edit['old']}")
                continue
            content = content.replace(edit["old"], edit["new"])
            logger.info(f"{edit['old']} -> {edit['new']}")

        file_path.write_text(content, encoding=encoding)
        logger.info(f"Successfully updated {file_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to update {filepath}: {e}")
        return False


def main():
    # Load environment variables from .env file
    load_dotenv()
    
    # Get API key from environment
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not found in .env file")
        print("Please create a .env file with: GEMINI_API_KEY=your_api_key_here")
        return
    
    # Set up paths
    base_dir = Path(__file__).parent
    operational_manual_path = base_dir / "OPERATIONAL_MANUAL_EDIT.md"
    os.chdir(config_dir)
    readme_path = "README.md"
    
    # Read instruction files
    operational_manual = read_file_content(operational_manual_path)
    readme_content = read_file_content(readme_path)
    
    if not operational_manual or not readme_content:
        print("Error: Could not load required instruction files")
        return

    # print(operational_manual)
    # print(readme_content)
    
    # Create system prompt from both files
    system_prompt = f"""You are G.H.O.S.T. (Guardian, Host, and Operational Scribe Tool).

    {operational_manual}

    ### CURRENT README.MD CONTENT:
    ```markdown
    {readme_content}
    ```

    Follow the operational manual strictly. Analyze user directives and output the updated README.md file accordingly.
    """
    
    # Initialize Gemini model
    llm = ChatGoogleGenerativeAI(
        model="gemini-flash-latest",
        google_api_key=api_key,
        temperature=0.1,
        convert_system_message_to_human=True
    )
    
    # Get user input
    print("=" * 60)
    print("G.H.O.S.T. v1 - Batserver Documentation Manager")
    print("=" * 60)
    print("\nEnter your directive (or 'quit' to exit):")
    print("-" * 60)
    
    user_input = input("\n> ").strip()
    
    if user_input.lower() in ['quit', 'exit', 'q']:
        print("Exiting G.H.O.S.T...")
        return
    
    if not user_input:
        print("Error: No input provided")
        return
    
    # Create messages
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_input)
    ]
    
    # Process with model
    print("\n" + "=" * 60)
    print("Processing directive...")
    print("=" * 60 + "\n")
    
    try:
        response = llm.invoke(messages).content
        result = json.loads(response)
        
        print("\n" + "=" * 60)
        print("PROPOSED CHANGES")
        print("=" * 60)
        print("-" * 60)
        print(response)
        print("-" * 60)

        edit_file_multiple(readme_path, result)
        print("README.md updated successfully")
        print("=" * 60 + "\n")

        diff = subprocess.run(["git", "diff", readme_path], capture_output=True, text=True)
        print("Differences:")
        print(diff.stdout)

        # Ask to keep or revert
        keep_choice = input("\nKeep these changes? (y/n) > ").strip().lower()

        if keep_choice not in ['y', 'yes']:
            # Revert the file
            subprocess.run(["git", "checkout", readme_path])
            print("✗ Changes reverted.")
            return

        print("✓ Changes kept!")

        # Commit choice
        commit_choice = input("\nDo you want to commit the changes? (y/n) > ").strip().lower()

        if commit_choice in ['y', 'yes']:

            commit_message = input("\nEnter the commit message > ").strip()
            if not commit_message:
                print("Error: Commit message cannot be empty")
                return

            # git add .
            add_result = subprocess.run(["git", "add", "."], capture_output=True, text=True)
            if add_result.returncode != 0:
                print(f"Error adding changes: {add_result.stderr}")
                print(add_result.stderr)
                return
            
            # git commit -m "{user_input}"
            commit_result =subprocess.run(["git", "commit", "-m", commit_message], capture_output=True, text=True)
            if commit_result.returncode != 0:
                print(f"Error committing changes: {commit_result.stderr}")
                print(commit_result.stderr)
                return

            print("\n✓ Changes committed successfully!")

            # git status
            status = subprocess.run(["git", "status"], capture_output=True, text=True)
            print(status.stdout)

            print("Changes Commited, Exiting...")
            return

        else:
            print("Changes not committed, Exiting...")
            return
        

        
        
        
        
    except Exception as e:
        print(f"Error processing request: {e}")
        return

if __name__ == "__main__":
    main()

