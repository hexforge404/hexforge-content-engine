import argparse

def parse_args():
    parser = argparse.ArgumentParser(description="Loop Prompt Generator with ComfyUI")
    
    parser.add_argument('--use_llava', action='store_true', help='Enable LLaVA for multimodal refinement')
    parser.add_argument('--max_seeds_total', type=int, default=3, help='Number of base seeds to explore')
    parser.add_argument('--max_seed_refinements', type=int, default=2, help='Max refinements per seed')
    parser.add_argument('--sleep', type=int, default=30, help='Seconds to wait after generation before scoring')
    parser.add_argument('--min_score', type=float, default=7.5, help='Minimum score required to continue')
    parser.add_argument('--retry', type=int, default=3, help='Number of retries on ComfyUI post failure')
    parser.add_argument('--final_variant_mode', type=str, default='best_prompt', help='Final variant strategy: best_prompt | custom')
    parser.add_argument('--project_name', type=str, default='default_project', help='Project name')
    parser.add_argument('--output_dir', type=str, default=None, help='Override output directory (optional)')
    
    args = parser.parse_args()
    
    if args.output_dir:
        print(f"Output directory overridden to: {args.output_dir}")
    else:
        print("Using default output directory.")
    
    print(f"Using project name: {args.project_name}")
    print(f"Using final variant mode: {args.final_variant_mode}")
    print(f"Using max seeds total: {args.max_seeds_total}")
    print(f"Using max seed refinements: {args.max_seed_refinements}")
    print(f"Using minimum score threshold: {args.min_score}")
    print(f"Using retry count: {args.retry}")
    print(f"Using sleep duration: {args.sleep} seconds")
    
    return args
