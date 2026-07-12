import os
import gc
import torch
from diffusers import (StableDiffusionXLPipeline, EulerAncestralDiscreteScheduler, EulerDiscreteScheduler, DPMSolverMultistepScheduler,
                       HeunDiscreteScheduler, KDPM2DiscreteScheduler, LMSDiscreteScheduler)


GLOBAL_MODEL_CACHE = {}


def optimize_pipeline(pipe):
    if not torch.cuda.is_available():
        print("未检到NVIDIA显卡")
        print("开启CPU模式运行")
        return pipe

    total_vram = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)

    if total_vram >= 14.0:
        pipe.to("cuda")
        print("开启极速模式")
    elif total_vram > 8:
        pipe.enable_model_cpu_offload()
        print("开启平衡模式")
    else:
        pipe.enable_sequential_cpu_offload()
        pipe.vae.enable_slicing()
        pipe.vae.enable_tiling()
        print("开启节能模式")

    try:
        pipe.enable_xformers_memory_efficient_attention()
        print("已开启efficient加速")
    except Exception as e:
        print("未开启efficient加速")
        print(e)

    return pipe


def set_sampler(pipe, sampler_name="euler_ancestral", scheduler="karras"):
    config = pipe.scheduler.config
    use_karras = (scheduler == "karras")

    if sampler_name == "euler":
        pipe.scheduler = EulerDiscreteScheduler.from_config(
            config,
            sigma_schedule=scheduler if scheduler in ["normal", "karras", "exponential", "sgm_uniform", "linear"] else "karras"
        )
    elif sampler_name == "euler_ancestral":
        pipe.scheduler = EulerAncestralDiscreteScheduler.from_config(
            config,
            sigma_schedule=scheduler if scheduler in ["normal", "karras", "exponential", "sgm_uniform", "linear"] else "karras"
        )
    elif sampler_name == "dpmpp_2m":
        pipe.scheduler = DPMSolverMultistepScheduler.from_config(
            config,
            use_karras_sigmas=use_karras
        )
    elif sampler_name == "dpmpp_2m_sde":
        pipe.scheduler = DPMSolverMultistepScheduler.from_config(
            config,
            use_karras_sigmas=use_karras,
            algorithm_type="sde-dpmsolver++"
        )
    elif sampler_name == "heun":
        pipe.scheduler = HeunDiscreteScheduler.from_config(
            config,
            sigma_schedule=scheduler if scheduler in ["normal", "karras", "exponential", "sgm_uniform", "linear"] else "karras"
        )
    elif sampler_name == "lms":
        pipe.scheduler = LMSDiscreteScheduler.from_config(
            config,
            sigma_schedule=scheduler if scheduler in ["normal", "karras", "exponential", "sgm_uniform", "linear"] else "karras"
        )
    return pipe


def load_sd_model(model_path):
    if model_path in GLOBAL_MODEL_CACHE:
        return GLOBAL_MODEL_CACHE[model_path]

    torch.cuda.empty_cache()
    gc.collect()

    print("模型加载中···")
    pipe = StableDiffusionXLPipeline.from_single_file(
        model_path,
        safety_checker=None,
        torch_dtype=torch.float16,
        use_safetensors=True,
    )
    print("模型加载完成%100")
    pipe = optimize_pipeline(pipe)

    GLOBAL_MODEL_CACHE[model_path] = pipe

    return GLOBAL_MODEL_CACHE[model_path]


def generate_image(pipe, prompt, negative_prompt, width, height, steps, cfg, seed, sampler_name, scheduler):
    print("图像开始生成！")
    pipe = set_sampler(pipe, sampler_name, scheduler)

    if seed == -1:
        generator = None
    else:
        generator = torch.Generator(device="cuda").manual_seed(seed)

    image = pipe(
        prompt=prompt,
        negative_prompt=negative_prompt,
        width=width,
        height=height,
        num_inference_steps=steps,
        guidance_scale=cfg,
        generator=generator
    ).images[0]
    print("图像生成完毕！")
    return image
