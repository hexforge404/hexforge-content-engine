from hexforge_prompt_runner.cli import parse_args
from hexforge_prompt_runner.config import load_config
from hexforge_prompt_runner.refinement import run_prompt_loop

def main():
    args = parse_args()
    config = load_config(args)
    run_prompt_loop(config)

if __name__ == "__main__":
    main()
