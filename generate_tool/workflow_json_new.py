# -*- coding: utf-8 -*-
# @File:     workflow_json.py
# @Author:   Wchime
# @DateTime: 2026/8/22 09:59

# minimax_h3 9张图片加上1个参考视频的背景音频
minimax_h3_9_image_1_video_json = {
  "115": {
    "inputs": {
      "aspect_ratio": "16:9 (Widescreen)",
      "megapixels": 0.5,
      "multiple": 32
    },
    "class_type": "ResolutionSelector",
    "_meta": {
      "title": "PASS1 / 16:9 / 0.5MP"
    }
  },
  "119": {
    "inputs": {
      "vae_name": "minimax_h3_video_vae_fp16.safetensors"
    },
    "class_type": "VAELoader",
    "_meta": {
      "title": "Load VAE"
    }
  },
  "120": {
    "inputs": {
      "vae_name": "minimax_h3_audio_vae_fp32.safetensors"
    },
    "class_type": "VAELoader",
    "_meta": {
      "title": "Load VAE"
    }
  },
  "123": {
    "inputs": {
      "sampler_name": "euler"
    },
    "class_type": "KSamplerSelect",
    "_meta": {
      "title": "KSamplerSelect"
    }
  },
  "124": {
    "inputs": {
      "scheduler": "simple",
      "steps": 10,
      "denoise": 1,
      "model": [
        "141",
        0
      ]
    },
    "class_type": "BasicScheduler",
    "_meta": {
      "title": "BasicScheduler"
    }
  },
  "125": {
    "inputs": {
      "noise": [
        "129",
        0
      ],
      "guider": [
        "126",
        0
      ],
      "sampler": [
        "123",
        0
      ],
      "sigmas": [
        "208",
        0
      ],
      "latent_image": [
        "136",
        1
      ]
    },
    "class_type": "SamplerCustomAdvanced",
    "_meta": {
      "title": "SamplerCustomAdvanced"
    }
  },
  "126": {
    "inputs": {
      "model": [
        "141",
        0
      ],
      "conditioning": [
        "136",
        0
      ]
    },
    "class_type": "BasicGuider",
    "_meta": {
      "title": "Basic Guider"
    }
  },
  "127": {
    "inputs": {
      "unet_name": "minimax_h3_hybrid_fl2va_ref2va_b25-49-int8.safetensors",
      "weight_dtype": "default"
    },
    "class_type": "UNETLoader",
    "_meta": {
      "title": "Load Diffusion Model"
    }
  },
  "128": {
    "inputs": {
      "clip_name": "qwen3vl_32b_minimax_h3_int8_convrot.safetensors",
      "type": "minimax",
      "device": "default"
    },
    "class_type": "CLIPLoader",
    "_meta": {
      "title": "Load CLIP"
    }
  },
  "129": {
    "inputs": {
      "noise_seed": 999
    },
    "class_type": "RandomNoise",
    "_meta": {
      "title": "RandomNoise"
    }
  },
  "131": {
    "inputs": {
      "expression": "max(5, round(a * 24)) + (5 - (max(5, round(a * 24)) % 17)) % 17",
      "values.a": [
        "132",
        0
      ]
    },
    "class_type": "ComfyMathExpression",
    "_meta": {
      "title": "Math Expression"
    }
  },
  "132": {
    "inputs": {
      "value": 6
    },
    "class_type": "PrimitiveFloat",
    "_meta": {
      "title": "Float (Duration)"
    }
  },
  "136": {
    "inputs": {
      "prompt": [
        "138",
        0
      ],
      "width": [
        "115",
        0
      ],
      "height": [
        "115",
        1
      ],
      "length": [
        "131",
        1
      ],
      "task_type": "auto",
      "audio_mode": "native",
      "audio_denoise_strength": 1,
      "add_source_as_reference": False,
      "prompt_primary_audio_ordinal": 0,
      "strict_prompt_tags": True,
      "ref_image_size": "match",
      "reference_video_policy": "official_2_to_15s",
      "allow_above_reference_area": True,
      "clip": [
        "128",
        0
      ],
      "video_vae": [
        "119",
        0
      ],
      "audio_vae": [
        "120",
        0
      ],
      "ref_images.ref_image_0": [
        "139",
        0
      ],
      "ref_images.ref_image_1": [
        "256",
        0
      ],
      "ref_images.ref_image_2": [
        "257",
        0
      ],
      "ref_images.ref_image_3": [
        "258",
        0
      ],
      "ref_images.ref_image_4": [
        "259",
        0
      ],
      "ref_images.ref_image_5": [
        "260",
        0
      ],
      "ref_images.ref_image_6": [
        "272",
        0
      ],
      "ref_images.ref_image_7": [
        "273",
        0
      ],
      "ref_images.ref_image_8": [
        "274",
        0
      ],
      "ref_audios.ref_audio_0": [
        "276",
        2
      ]
    },
    "class_type": "MiniMaxH3AudioConditioningT8",
    "_meta": {
      "title": "T8 条件节点｜通用模式"
    }
  },
  "138": {
    "inputs": {
      "value": "subject_definitions:\\n<Subject 1> is Lin Che from <Picture 1>, a 29-year-old Chinese woman with a chin-length black bob, a small mole at the outer end of her left eyebrow, a dark red buttoned knitted cardigan over a white crew-neck top and black trousers. Preserve her facial identity, natural skin and wardrobe; the three standing views do not dictate her seated performance.\\n<Subject 2> is Chen Li from <Picture 2>, a 48-year-old Chinese man with a square face, short black hair graying at the temples, a slight gap in his right eyebrow, a medium-gray knitted cardigan over a pale blue shirt and dark gray trousers. Preserve his face, age, hair and clothing, not the reference pose.\\n<Subject 3> is the same empty meeting room from <Picture 3>: a matte light-gray rectangular table with its long axis east-west, one chair at each east and west short end, a closed high frosted window in the north wall, a low dark-green six-cubby cabinet against the west wall and a closed brown door in the south wall. Preserve the world-space layout and matte surfaces. Omit the four-view borders, reference viewpoints and incidental objects; the room contains only the two directed people and the one directed recorder.\\n\\nsummary:\\n[reference generation] A 6-second continuous live-action medium shot in <Subject 3>. Lin Che establishes that the recorder is already running and challenges Chen Li to speak on record. The three pictures supply identity and room design, with newly directed framing rather than exact endpoints.\\n\\nretention_analysis:\\n<Subject 1> (appears in [Shot 1]): fully_preserved - Keep Lin Che's identity, bob, dark red cardigan and white inner top while directing the specified seated performance.\\n<Subject 2> (appears in [Shot 1]): fully_preserved - Keep Chen Li's identity, gray temples, gray cardigan and pale blue shirt; the directed seated pose replaces the standing reference.\\n<Subject 3> (appears in [Shot 1]): partially_preserved - Keep the fixed room topology, north-window light, west cabinet and table material; omit multi-view panels and reference framing. The initial camera composition is newly directed.\\n\\ndetailed_description:\\nThe target video is a restrained contemporary Chinese live-action suspense drama, with natural skin texture, readable faces and softly lit matte surfaces.\\n[Shot 1] The camera occupies the open southeast aisle at approximately (1.5,-1.5,1.3) meters relative to the table center and faces northwest toward <Subject 1>. She is seated at the west end on screen-left, torso and head turned east toward <Subject 2>, with her gaze going screen-right. Her chin-length bob, natural eyebrow mark and dark red cardigan remain visible. His gray-clad shoulder and pale blue collar occupy only the extreme right foreground; his body remains at the east seat, and his shoulder does not obscure her face, hands or the recorder. The background shows the west green cabinet and only a geometrically plausible part of the north wall and window. The south door stays behind the camera and out of frame.\\nBoth remain seated on the same two chairs, feet on the floor, with neither changing seats or turning away. <Subject 1>'s two empty hands rest separately on the west table edge; <Subject 2>'s left hand rests on the east edge. There is exactly one small black rectangular audio recorder, about 10 by 3 by 1 centimeters, lying flat on the matte tabletop, long axis east-west and its single red indicator steadily lit. It has no readable display. Its center is 0.35 meters east and 0.12 meters south of the table center. His right fingertips rest on the tabletop three centimeters east of the recorder, separated from its casing. The recorder and both hands remain still until any explicitly directed action.\\nHold the initial pose for about one second. <Subject 1> (S1), using a clear low young-adult female Mandarin voice, measured and direct, says <d>[Chinese] 录音开着。你还要我关掉？</d> The statement about recording is a condition of this conversation, not a command to press a button. Finish speaking by about 4.5 seconds, close the mouth and hold eye contact for the remaining beat. Only speech-related lips, small facial tension and natural breathing change. The listener keeps a closed mouth and still hands. No control is pressed, and the indicator remains steadily red.\\nThe sole key is diffused cool-neutral daylight from the fixed high north window, above seated eye level. It softly illuminates the north-facing cheek, the upper knuckles and the recorder's top plane. Weak, slightly warm bounce from the south wall preserves detail on the shadow side without creating another hard shadow. Hair casts a gentle edge at the jaw, and sleeves retain soft folds. Small contact shadows attach hands and the recorder to the tabletop and extend toward the south in world space; the stationary recorder retains a stationary contact shadow. Keep source positions, exposure and white balance steady. Matte surfaces produce subdued highlights rather than flashes. Changing the viewpoint must not relocate the light to the camera side.\\nUse a 40 mm-equivalent lens at seated eye height, in a medium composition with enough depth of field for the featured face, hands and recorder to remain legible. Focus stays on the featured person's eyes without a focus pull. The camera remains fixed throughout; position, orientation, focal length and framing stay unchanged. The foreground shoulder remains a narrow edge element, not a moving wipe or obstruction. Keep the same single shot from beginning to end.\\nThe output is one full-frame scene, with no reference panels, additional people, automatic captions or decorative overlays. Preserve the settled end pose for the adjacent reverse-angle cut.\\n\\noverall_soundscape:\\nLow steady ventilation and distant, muffled room ambience, with subtle breaths and fabric noise. The stationary recorder produces no playback, beeps or repeated scrape. Keep the room tone unobtrusive beneath the voice.\\n\\nnon_diegetic_music:\\nN/A"
    },
    "class_type": "PrimitiveStringMultiline",
    "_meta": {
      "title": "Input Text (Prompt)"
    }
  },
  "139": {
    "inputs": {
      "image": "2636c786c4c0e6c33db28ba14bbe1c381ed4f7cbd8ae925b745e370640e55fea.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "141": {
    "inputs": {
      "max_resolution": 1024,
      "jpeg_quality": 80,
      "suppress_default_preview": True,
      "preview_frames": [
        "131",
        1
      ],
      "preview_fps": 12,
      "tiny_vae": "taeh3.safetensors",
      "model": [
        "178",
        0
      ]
    },
    "class_type": "ModelPreviewOverrideKJ",
    "_meta": {
      "title": "Model Preview Override KJ"
    }
  },
  "147": {
    "inputs": {
      "lora_name": "minimax_h3_ref2v_turbo_8step_v1.0_768p_comfyui_bf16.safetensors",
      "strength_model": 1.0000000000000002,
      "model": [
        "127",
        0
      ]
    },
    "class_type": "LoraLoaderModelOnly",
    "_meta": {
      "title": "Load LoRA"
    }
  },
  "149": {
    "inputs": {
      "shift_video": 12,
      "shift_audio": 3,
      "model": [
        "147",
        0
      ]
    },
    "class_type": "MiniMaxH3SigmaShift",
    "_meta": {
      "title": "ModelSamplingMiniMaxH3"
    }
  },
  "178": {
    "inputs": {
      "attention": "comfy kitchen attention",
      "model": [
        "149",
        0
      ]
    },
    "class_type": "ModelAttentionBackend",
    "_meta": {
      "title": "ModelAttentionBackend"
    }
  },
  "208": {
    "inputs": {
      "step": 6,
      "sigmas": [
        "254",
        0
      ]
    },
    "class_type": "SplitSigmas",
    "_meta": {
      "title": "SplitSigmas"
    }
  },
  "209": {
    "inputs": {
      "noise": [
        "129",
        0
      ],
      "guider": [
        "126",
        0
      ],
      "sampler": [
        "123",
        0
      ],
      "sigmas": [
        "208",
        1
      ],
      "latent_image": [
        "212",
        0
      ]
    },
    "class_type": "SamplerCustomAdvanced",
    "_meta": {
      "title": "SamplerCustomAdvanced"
    }
  },
  "211": {
    "inputs": {
      "av_latent": [
        "125",
        1
      ]
    },
    "class_type": "LTXVSeparateAVLatent",
    "_meta": {
      "title": "Separate AV Latent"
    }
  },
  "212": {
    "inputs": {
      "video_latent": [
        "263",
        0
      ],
      "audio_latent": [
        "211",
        1
      ]
    },
    "class_type": "LTXVConcatAVLatent",
    "_meta": {
      "title": "Concat AV Latent"
    }
  },
  "218": {
    "inputs": {
      "samples": [
        "209",
        0
      ],
      "vae": [
        "120",
        0
      ]
    },
    "class_type": "VAEDecodeAudio",
    "_meta": {
      "title": "VAE Decode Audio"
    }
  },
  "219": {
    "inputs": {
      "samples": [
        "209",
        0
      ],
      "vae": [
        "119",
        0
      ]
    },
    "class_type": "VAEDecode",
    "_meta": {
      "title": "VAE Decode"
    }
  },
  "254": {
    "inputs": {
      "extra_steps": 1,
      "start_at_sigma": 0.7,
      "end_at_sigma": 0,
      "spacing": "cosine",
      "sigmas": [
        "124",
        0
      ]
    },
    "class_type": "H3SigmaRefiner",
    "_meta": {
      "title": "H3 Sigma Refiner"
    }
  },
  "256": {
    "inputs": {
      "image": "07d2e1d22673808899bba100354351b0d4b5b723a10358c7a9ffe92ec0c98ddc.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "257": {
    "inputs": {
      "image": "56a596334282d0057a0847e7a1f2714e8aa27725718b5a162e3ac33c02e42b17.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "258": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "259": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "260": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "263": {
    "inputs": {
      "model_name": "minimax_h3_latent_upscaler_3d_fp16.safetensors",
      "mode": "scale by multiplier",
      "mode.scale": 2,
      "align": 32,
      "device": "cuda",
      "precision": "fp16",
      "enable_chunking": True,
      "latent": [
        "211",
        0
      ]
    },
    "class_type": "MinimaxH3LatentUpscaler3D",
    "_meta": {
      "title": "Minimax H3 Latent Upscaler (3D)"
    }
  },
  "271": {
    "inputs": {
      "frame_rate": 24,
      "loop_count": 0,
      "filename_prefix": "第二次采样",
      "format": "video/h264-mp4",
      "pix_fmt": "yuv420p",
      "crf": 19,
      "save_metadata": True,
      "trim_to_audio": False,
      "pingpong": False,
      "save_output": True,
      "no_preview": False,
      "images": [
        "219",
        0
      ],
      "audio": [
        "218",
        0
      ]
    },
    "class_type": "VHS_VideoCombine",
    "_meta": {
      "title": "Video Combine 🎥🅥🅗🅢"
    }
  },
  "272": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "273": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "274": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "276": {
    "inputs": {
      "video": "1657d341db3688d8d05445f775e8692a0041b27116db8b746fbc5c96a829deb1.mp4",
      "force_rate": 24,
      "force_size": "Disabled",
      "custom_width": 0,
      "custom_height": 0,
      "frame_load_cap": 0,
      "skip_first_frames": 0,
      "select_every_nth": 1,
      "format": "AnimateDiff"
    },
    "class_type": "VHS_LoadVideo",
    "_meta": {
      "title": "Load Video (Upload) 🎥🅥🅗🅢"
    }
  }
}

# minimax_h3 8张图片加上1个参考视频的背景音频
minimax_h3_8_image_1_video_json = {
  "115": {
    "inputs": {
      "aspect_ratio": "16:9 (Widescreen)",
      "megapixels": 0.5,
      "multiple": 32
    },
    "class_type": "ResolutionSelector",
    "_meta": {
      "title": "PASS1 / 16:9 / 0.5MP"
    }
  },
  "119": {
    "inputs": {
      "vae_name": "minimax_h3_video_vae_fp16.safetensors"
    },
    "class_type": "VAELoader",
    "_meta": {
      "title": "Load VAE"
    }
  },
  "120": {
    "inputs": {
      "vae_name": "minimax_h3_audio_vae_fp32.safetensors"
    },
    "class_type": "VAELoader",
    "_meta": {
      "title": "Load VAE"
    }
  },
  "123": {
    "inputs": {
      "sampler_name": "euler"
    },
    "class_type": "KSamplerSelect",
    "_meta": {
      "title": "KSamplerSelect"
    }
  },
  "124": {
    "inputs": {
      "scheduler": "simple",
      "steps": 10,
      "denoise": 1,
      "model": [
        "141",
        0
      ]
    },
    "class_type": "BasicScheduler",
    "_meta": {
      "title": "BasicScheduler"
    }
  },
  "125": {
    "inputs": {
      "noise": [
        "129",
        0
      ],
      "guider": [
        "126",
        0
      ],
      "sampler": [
        "123",
        0
      ],
      "sigmas": [
        "208",
        0
      ],
      "latent_image": [
        "136",
        1
      ]
    },
    "class_type": "SamplerCustomAdvanced",
    "_meta": {
      "title": "SamplerCustomAdvanced"
    }
  },
  "126": {
    "inputs": {
      "model": [
        "141",
        0
      ],
      "conditioning": [
        "136",
        0
      ]
    },
    "class_type": "BasicGuider",
    "_meta": {
      "title": "Basic Guider"
    }
  },
  "127": {
    "inputs": {
      "unet_name": "minimax_h3_hybrid_fl2va_ref2va_b25-49-int8.safetensors",
      "weight_dtype": "default"
    },
    "class_type": "UNETLoader",
    "_meta": {
      "title": "Load Diffusion Model"
    }
  },
  "128": {
    "inputs": {
      "clip_name": "qwen3vl_32b_minimax_h3_int8_convrot.safetensors",
      "type": "minimax",
      "device": "default"
    },
    "class_type": "CLIPLoader",
    "_meta": {
      "title": "Load CLIP"
    }
  },
  "129": {
    "inputs": {
      "noise_seed": 999
    },
    "class_type": "RandomNoise",
    "_meta": {
      "title": "RandomNoise"
    }
  },
  "131": {
    "inputs": {
      "expression": "max(5, round(a * 24)) + (5 - (max(5, round(a * 24)) % 17)) % 17",
      "values.a": [
        "132",
        0
      ]
    },
    "class_type": "ComfyMathExpression",
    "_meta": {
      "title": "Math Expression"
    }
  },
  "132": {
    "inputs": {
      "value": 6
    },
    "class_type": "PrimitiveFloat",
    "_meta": {
      "title": "Float (Duration)"
    }
  },
  "136": {
    "inputs": {
      "prompt": [
        "138",
        0
      ],
      "width": [
        "115",
        0
      ],
      "height": [
        "115",
        1
      ],
      "length": [
        "131",
        1
      ],
      "task_type": "auto",
      "audio_mode": "native",
      "audio_denoise_strength": 1,
      "add_source_as_reference": False,
      "prompt_primary_audio_ordinal": 0,
      "strict_prompt_tags": True,
      "ref_image_size": "match",
      "reference_video_policy": "official_2_to_15s",
      "allow_above_reference_area": True,
      "clip": [
        "128",
        0
      ],
      "video_vae": [
        "119",
        0
      ],
      "audio_vae": [
        "120",
        0
      ],
      "ref_images.ref_image_0": [
        "139",
        0
      ],
      "ref_images.ref_image_1": [
        "256",
        0
      ],
      "ref_images.ref_image_2": [
        "257",
        0
      ],
      "ref_images.ref_image_3": [
        "258",
        0
      ],
      "ref_images.ref_image_4": [
        "259",
        0
      ],
      "ref_images.ref_image_5": [
        "260",
        0
      ],
      "ref_images.ref_image_6": [
        "272",
        0
      ],
      "ref_images.ref_image_7": [
        "273",
        0
      ],
      "ref_audios.ref_audio_0": [
        "276",
        2
      ]
    },
    "class_type": "MiniMaxH3AudioConditioningT8",
    "_meta": {
      "title": "T8 条件节点｜通用模式"
    }
  },
  "138": {
    "inputs": {
      "value": "subject_definitions:\\n<Subject 1> is Lin Che from <Picture 1>, a 29-year-old Chinese woman with a chin-length black bob, a small mole at the outer end of her left eyebrow, a dark red buttoned knitted cardigan over a white crew-neck top and black trousers. Preserve her facial identity, natural skin and wardrobe; the three standing views do not dictate her seated performance.\\n<Subject 2> is Chen Li from <Picture 2>, a 48-year-old Chinese man with a square face, short black hair graying at the temples, a slight gap in his right eyebrow, a medium-gray knitted cardigan over a pale blue shirt and dark gray trousers. Preserve his face, age, hair and clothing, not the reference pose.\\n<Subject 3> is the same empty meeting room from <Picture 3>: a matte light-gray rectangular table with its long axis east-west, one chair at each east and west short end, a closed high frosted window in the north wall, a low dark-green six-cubby cabinet against the west wall and a closed brown door in the south wall. Preserve the world-space layout and matte surfaces. Omit the four-view borders, reference viewpoints and incidental objects; the room contains only the two directed people and the one directed recorder.\\n\\nsummary:\\n[reference generation] A 6-second continuous live-action medium shot in <Subject 3>. Lin Che establishes that the recorder is already running and challenges Chen Li to speak on record. The three pictures supply identity and room design, with newly directed framing rather than exact endpoints.\\n\\nretention_analysis:\\n<Subject 1> (appears in [Shot 1]): fully_preserved - Keep Lin Che's identity, bob, dark red cardigan and white inner top while directing the specified seated performance.\\n<Subject 2> (appears in [Shot 1]): fully_preserved - Keep Chen Li's identity, gray temples, gray cardigan and pale blue shirt; the directed seated pose replaces the standing reference.\\n<Subject 3> (appears in [Shot 1]): partially_preserved - Keep the fixed room topology, north-window light, west cabinet and table material; omit multi-view panels and reference framing. The initial camera composition is newly directed.\\n\\ndetailed_description:\\nThe target video is a restrained contemporary Chinese live-action suspense drama, with natural skin texture, readable faces and softly lit matte surfaces.\\n[Shot 1] The camera occupies the open southeast aisle at approximately (1.5,-1.5,1.3) meters relative to the table center and faces northwest toward <Subject 1>. She is seated at the west end on screen-left, torso and head turned east toward <Subject 2>, with her gaze going screen-right. Her chin-length bob, natural eyebrow mark and dark red cardigan remain visible. His gray-clad shoulder and pale blue collar occupy only the extreme right foreground; his body remains at the east seat, and his shoulder does not obscure her face, hands or the recorder. The background shows the west green cabinet and only a geometrically plausible part of the north wall and window. The south door stays behind the camera and out of frame.\\nBoth remain seated on the same two chairs, feet on the floor, with neither changing seats or turning away. <Subject 1>'s two empty hands rest separately on the west table edge; <Subject 2>'s left hand rests on the east edge. There is exactly one small black rectangular audio recorder, about 10 by 3 by 1 centimeters, lying flat on the matte tabletop, long axis east-west and its single red indicator steadily lit. It has no readable display. Its center is 0.35 meters east and 0.12 meters south of the table center. His right fingertips rest on the tabletop three centimeters east of the recorder, separated from its casing. The recorder and both hands remain still until any explicitly directed action.\\nHold the initial pose for about one second. <Subject 1> (S1), using a clear low young-adult female Mandarin voice, measured and direct, says <d>[Chinese] 录音开着。你还要我关掉？</d> The statement about recording is a condition of this conversation, not a command to press a button. Finish speaking by about 4.5 seconds, close the mouth and hold eye contact for the remaining beat. Only speech-related lips, small facial tension and natural breathing change. The listener keeps a closed mouth and still hands. No control is pressed, and the indicator remains steadily red.\\nThe sole key is diffused cool-neutral daylight from the fixed high north window, above seated eye level. It softly illuminates the north-facing cheek, the upper knuckles and the recorder's top plane. Weak, slightly warm bounce from the south wall preserves detail on the shadow side without creating another hard shadow. Hair casts a gentle edge at the jaw, and sleeves retain soft folds. Small contact shadows attach hands and the recorder to the tabletop and extend toward the south in world space; the stationary recorder retains a stationary contact shadow. Keep source positions, exposure and white balance steady. Matte surfaces produce subdued highlights rather than flashes. Changing the viewpoint must not relocate the light to the camera side.\\nUse a 40 mm-equivalent lens at seated eye height, in a medium composition with enough depth of field for the featured face, hands and recorder to remain legible. Focus stays on the featured person's eyes without a focus pull. The camera remains fixed throughout; position, orientation, focal length and framing stay unchanged. The foreground shoulder remains a narrow edge element, not a moving wipe or obstruction. Keep the same single shot from beginning to end.\\nThe output is one full-frame scene, with no reference panels, additional people, automatic captions or decorative overlays. Preserve the settled end pose for the adjacent reverse-angle cut.\\n\\noverall_soundscape:\\nLow steady ventilation and distant, muffled room ambience, with subtle breaths and fabric noise. The stationary recorder produces no playback, beeps or repeated scrape. Keep the room tone unobtrusive beneath the voice.\\n\\nnon_diegetic_music:\\nN/A"
    },
    "class_type": "PrimitiveStringMultiline",
    "_meta": {
      "title": "Input Text (Prompt)"
    }
  },
  "139": {
    "inputs": {
      "image": "2636c786c4c0e6c33db28ba14bbe1c381ed4f7cbd8ae925b745e370640e55fea.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "141": {
    "inputs": {
      "max_resolution": 1024,
      "jpeg_quality": 80,
      "suppress_default_preview": True,
      "preview_frames": [
        "131",
        1
      ],
      "preview_fps": 12,
      "tiny_vae": "taeh3.safetensors",
      "model": [
        "178",
        0
      ]
    },
    "class_type": "ModelPreviewOverrideKJ",
    "_meta": {
      "title": "Model Preview Override KJ"
    }
  },
  "147": {
    "inputs": {
      "lora_name": "minimax_h3_ref2v_turbo_8step_v1.0_768p_comfyui_bf16.safetensors",
      "strength_model": 1.0000000000000002,
      "model": [
        "127",
        0
      ]
    },
    "class_type": "LoraLoaderModelOnly",
    "_meta": {
      "title": "Load LoRA"
    }
  },
  "149": {
    "inputs": {
      "shift_video": 12,
      "shift_audio": 3,
      "model": [
        "147",
        0
      ]
    },
    "class_type": "MiniMaxH3SigmaShift",
    "_meta": {
      "title": "ModelSamplingMiniMaxH3"
    }
  },
  "178": {
    "inputs": {
      "attention": "comfy kitchen attention",
      "model": [
        "149",
        0
      ]
    },
    "class_type": "ModelAttentionBackend",
    "_meta": {
      "title": "ModelAttentionBackend"
    }
  },
  "208": {
    "inputs": {
      "step": 6,
      "sigmas": [
        "254",
        0
      ]
    },
    "class_type": "SplitSigmas",
    "_meta": {
      "title": "SplitSigmas"
    }
  },
  "209": {
    "inputs": {
      "noise": [
        "129",
        0
      ],
      "guider": [
        "126",
        0
      ],
      "sampler": [
        "123",
        0
      ],
      "sigmas": [
        "208",
        1
      ],
      "latent_image": [
        "212",
        0
      ]
    },
    "class_type": "SamplerCustomAdvanced",
    "_meta": {
      "title": "SamplerCustomAdvanced"
    }
  },
  "211": {
    "inputs": {
      "av_latent": [
        "125",
        1
      ]
    },
    "class_type": "LTXVSeparateAVLatent",
    "_meta": {
      "title": "Separate AV Latent"
    }
  },
  "212": {
    "inputs": {
      "video_latent": [
        "263",
        0
      ],
      "audio_latent": [
        "211",
        1
      ]
    },
    "class_type": "LTXVConcatAVLatent",
    "_meta": {
      "title": "Concat AV Latent"
    }
  },
  "218": {
    "inputs": {
      "samples": [
        "209",
        0
      ],
      "vae": [
        "120",
        0
      ]
    },
    "class_type": "VAEDecodeAudio",
    "_meta": {
      "title": "VAE Decode Audio"
    }
  },
  "219": {
    "inputs": {
      "samples": [
        "209",
        0
      ],
      "vae": [
        "119",
        0
      ]
    },
    "class_type": "VAEDecode",
    "_meta": {
      "title": "VAE Decode"
    }
  },
  "254": {
    "inputs": {
      "extra_steps": 1,
      "start_at_sigma": 0.7,
      "end_at_sigma": 0,
      "spacing": "cosine",
      "sigmas": [
        "124",
        0
      ]
    },
    "class_type": "H3SigmaRefiner",
    "_meta": {
      "title": "H3 Sigma Refiner"
    }
  },
  "256": {
    "inputs": {
      "image": "07d2e1d22673808899bba100354351b0d4b5b723a10358c7a9ffe92ec0c98ddc.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "257": {
    "inputs": {
      "image": "56a596334282d0057a0847e7a1f2714e8aa27725718b5a162e3ac33c02e42b17.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "258": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "259": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "260": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "263": {
    "inputs": {
      "model_name": "minimax_h3_latent_upscaler_3d_fp16.safetensors",
      "mode": "scale by multiplier",
      "mode.scale": 2,
      "align": 32,
      "device": "cuda",
      "precision": "fp16",
      "enable_chunking": True,
      "latent": [
        "211",
        0
      ]
    },
    "class_type": "MinimaxH3LatentUpscaler3D",
    "_meta": {
      "title": "Minimax H3 Latent Upscaler (3D)"
    }
  },
  "271": {
    "inputs": {
      "frame_rate": 24,
      "loop_count": 0,
      "filename_prefix": "第二次采样",
      "format": "video/h264-mp4",
      "pix_fmt": "yuv420p",
      "crf": 19,
      "save_metadata": True,
      "trim_to_audio": False,
      "pingpong": False,
      "save_output": True,
      "no_preview": False,
      "images": [
        "219",
        0
      ],
      "audio": [
        "218",
        0
      ]
    },
    "class_type": "VHS_VideoCombine",
    "_meta": {
      "title": "Video Combine 🎥🅥🅗🅢"
    }
  },
  "272": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "273": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "274": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "276": {
    "inputs": {
      "video": "1657d341db3688d8d05445f775e8692a0041b27116db8b746fbc5c96a829deb1.mp4",
      "force_rate": 24,
      "force_size": "Disabled",
      "custom_width": 0,
      "custom_height": 0,
      "frame_load_cap": 0,
      "skip_first_frames": 0,
      "select_every_nth": 1,
      "format": "AnimateDiff"
    },
    "class_type": "VHS_LoadVideo",
    "_meta": {
      "title": "Load Video (Upload) 🎥🅥🅗🅢"
    }
  }
}

# minimax_h3 7张图片加上1个参考视频的背景音频
minimax_h3_7_image_1_video_json = {
  "115": {
    "inputs": {
      "aspect_ratio": "16:9 (Widescreen)",
      "megapixels": 0.5,
      "multiple": 32
    },
    "class_type": "ResolutionSelector",
    "_meta": {
      "title": "PASS1 / 16:9 / 0.5MP"
    }
  },
  "119": {
    "inputs": {
      "vae_name": "minimax_h3_video_vae_fp16.safetensors"
    },
    "class_type": "VAELoader",
    "_meta": {
      "title": "Load VAE"
    }
  },
  "120": {
    "inputs": {
      "vae_name": "minimax_h3_audio_vae_fp32.safetensors"
    },
    "class_type": "VAELoader",
    "_meta": {
      "title": "Load VAE"
    }
  },
  "123": {
    "inputs": {
      "sampler_name": "euler"
    },
    "class_type": "KSamplerSelect",
    "_meta": {
      "title": "KSamplerSelect"
    }
  },
  "124": {
    "inputs": {
      "scheduler": "simple",
      "steps": 10,
      "denoise": 1,
      "model": [
        "141",
        0
      ]
    },
    "class_type": "BasicScheduler",
    "_meta": {
      "title": "BasicScheduler"
    }
  },
  "125": {
    "inputs": {
      "noise": [
        "129",
        0
      ],
      "guider": [
        "126",
        0
      ],
      "sampler": [
        "123",
        0
      ],
      "sigmas": [
        "208",
        0
      ],
      "latent_image": [
        "136",
        1
      ]
    },
    "class_type": "SamplerCustomAdvanced",
    "_meta": {
      "title": "SamplerCustomAdvanced"
    }
  },
  "126": {
    "inputs": {
      "model": [
        "141",
        0
      ],
      "conditioning": [
        "136",
        0
      ]
    },
    "class_type": "BasicGuider",
    "_meta": {
      "title": "Basic Guider"
    }
  },
  "127": {
    "inputs": {
      "unet_name": "minimax_h3_hybrid_fl2va_ref2va_b25-49-int8.safetensors",
      "weight_dtype": "default"
    },
    "class_type": "UNETLoader",
    "_meta": {
      "title": "Load Diffusion Model"
    }
  },
  "128": {
    "inputs": {
      "clip_name": "qwen3vl_32b_minimax_h3_int8_convrot.safetensors",
      "type": "minimax",
      "device": "default"
    },
    "class_type": "CLIPLoader",
    "_meta": {
      "title": "Load CLIP"
    }
  },
  "129": {
    "inputs": {
      "noise_seed": 999
    },
    "class_type": "RandomNoise",
    "_meta": {
      "title": "RandomNoise"
    }
  },
  "131": {
    "inputs": {
      "expression": "max(5, round(a * 24)) + (5 - (max(5, round(a * 24)) % 17)) % 17",
      "values.a": [
        "132",
        0
      ]
    },
    "class_type": "ComfyMathExpression",
    "_meta": {
      "title": "Math Expression"
    }
  },
  "132": {
    "inputs": {
      "value": 6
    },
    "class_type": "PrimitiveFloat",
    "_meta": {
      "title": "Float (Duration)"
    }
  },
  "136": {
    "inputs": {
      "prompt": [
        "138",
        0
      ],
      "width": [
        "115",
        0
      ],
      "height": [
        "115",
        1
      ],
      "length": [
        "131",
        1
      ],
      "task_type": "auto",
      "audio_mode": "native",
      "audio_denoise_strength": 1,
      "add_source_as_reference": False,
      "prompt_primary_audio_ordinal": 0,
      "strict_prompt_tags": True,
      "ref_image_size": "match",
      "reference_video_policy": "official_2_to_15s",
      "allow_above_reference_area": True,
      "clip": [
        "128",
        0
      ],
      "video_vae": [
        "119",
        0
      ],
      "audio_vae": [
        "120",
        0
      ],
      "ref_images.ref_image_0": [
        "139",
        0
      ],
      "ref_images.ref_image_1": [
        "256",
        0
      ],
      "ref_images.ref_image_2": [
        "257",
        0
      ],
      "ref_images.ref_image_3": [
        "258",
        0
      ],
      "ref_images.ref_image_4": [
        "259",
        0
      ],
      "ref_images.ref_image_5": [
        "260",
        0
      ],
      "ref_images.ref_image_6": [
        "272",
        0
      ],
      "ref_audios.ref_audio_0": [
        "276",
        2
      ]
    },
    "class_type": "MiniMaxH3AudioConditioningT8",
    "_meta": {
      "title": "T8 条件节点｜通用模式"
    }
  },
  "138": {
    "inputs": {
      "value": "subject_definitions:\\n<Subject 1> is Lin Che from <Picture 1>, a 29-year-old Chinese woman with a chin-length black bob, a small mole at the outer end of her left eyebrow, a dark red buttoned knitted cardigan over a white crew-neck top and black trousers. Preserve her facial identity, natural skin and wardrobe; the three standing views do not dictate her seated performance.\\n<Subject 2> is Chen Li from <Picture 2>, a 48-year-old Chinese man with a square face, short black hair graying at the temples, a slight gap in his right eyebrow, a medium-gray knitted cardigan over a pale blue shirt and dark gray trousers. Preserve his face, age, hair and clothing, not the reference pose.\\n<Subject 3> is the same empty meeting room from <Picture 3>: a matte light-gray rectangular table with its long axis east-west, one chair at each east and west short end, a closed high frosted window in the north wall, a low dark-green six-cubby cabinet against the west wall and a closed brown door in the south wall. Preserve the world-space layout and matte surfaces. Omit the four-view borders, reference viewpoints and incidental objects; the room contains only the two directed people and the one directed recorder.\\n\\nsummary:\\n[reference generation] A 6-second continuous live-action medium shot in <Subject 3>. Lin Che establishes that the recorder is already running and challenges Chen Li to speak on record. The three pictures supply identity and room design, with newly directed framing rather than exact endpoints.\\n\\nretention_analysis:\\n<Subject 1> (appears in [Shot 1]): fully_preserved - Keep Lin Che's identity, bob, dark red cardigan and white inner top while directing the specified seated performance.\\n<Subject 2> (appears in [Shot 1]): fully_preserved - Keep Chen Li's identity, gray temples, gray cardigan and pale blue shirt; the directed seated pose replaces the standing reference.\\n<Subject 3> (appears in [Shot 1]): partially_preserved - Keep the fixed room topology, north-window light, west cabinet and table material; omit multi-view panels and reference framing. The initial camera composition is newly directed.\\n\\ndetailed_description:\\nThe target video is a restrained contemporary Chinese live-action suspense drama, with natural skin texture, readable faces and softly lit matte surfaces.\\n[Shot 1] The camera occupies the open southeast aisle at approximately (1.5,-1.5,1.3) meters relative to the table center and faces northwest toward <Subject 1>. She is seated at the west end on screen-left, torso and head turned east toward <Subject 2>, with her gaze going screen-right. Her chin-length bob, natural eyebrow mark and dark red cardigan remain visible. His gray-clad shoulder and pale blue collar occupy only the extreme right foreground; his body remains at the east seat, and his shoulder does not obscure her face, hands or the recorder. The background shows the west green cabinet and only a geometrically plausible part of the north wall and window. The south door stays behind the camera and out of frame.\\nBoth remain seated on the same two chairs, feet on the floor, with neither changing seats or turning away. <Subject 1>'s two empty hands rest separately on the west table edge; <Subject 2>'s left hand rests on the east edge. There is exactly one small black rectangular audio recorder, about 10 by 3 by 1 centimeters, lying flat on the matte tabletop, long axis east-west and its single red indicator steadily lit. It has no readable display. Its center is 0.35 meters east and 0.12 meters south of the table center. His right fingertips rest on the tabletop three centimeters east of the recorder, separated from its casing. The recorder and both hands remain still until any explicitly directed action.\\nHold the initial pose for about one second. <Subject 1> (S1), using a clear low young-adult female Mandarin voice, measured and direct, says <d>[Chinese] 录音开着。你还要我关掉？</d> The statement about recording is a condition of this conversation, not a command to press a button. Finish speaking by about 4.5 seconds, close the mouth and hold eye contact for the remaining beat. Only speech-related lips, small facial tension and natural breathing change. The listener keeps a closed mouth and still hands. No control is pressed, and the indicator remains steadily red.\\nThe sole key is diffused cool-neutral daylight from the fixed high north window, above seated eye level. It softly illuminates the north-facing cheek, the upper knuckles and the recorder's top plane. Weak, slightly warm bounce from the south wall preserves detail on the shadow side without creating another hard shadow. Hair casts a gentle edge at the jaw, and sleeves retain soft folds. Small contact shadows attach hands and the recorder to the tabletop and extend toward the south in world space; the stationary recorder retains a stationary contact shadow. Keep source positions, exposure and white balance steady. Matte surfaces produce subdued highlights rather than flashes. Changing the viewpoint must not relocate the light to the camera side.\\nUse a 40 mm-equivalent lens at seated eye height, in a medium composition with enough depth of field for the featured face, hands and recorder to remain legible. Focus stays on the featured person's eyes without a focus pull. The camera remains fixed throughout; position, orientation, focal length and framing stay unchanged. The foreground shoulder remains a narrow edge element, not a moving wipe or obstruction. Keep the same single shot from beginning to end.\\nThe output is one full-frame scene, with no reference panels, additional people, automatic captions or decorative overlays. Preserve the settled end pose for the adjacent reverse-angle cut.\\n\\noverall_soundscape:\\nLow steady ventilation and distant, muffled room ambience, with subtle breaths and fabric noise. The stationary recorder produces no playback, beeps or repeated scrape. Keep the room tone unobtrusive beneath the voice.\\n\\nnon_diegetic_music:\\nN/A"
    },
    "class_type": "PrimitiveStringMultiline",
    "_meta": {
      "title": "Input Text (Prompt)"
    }
  },
  "139": {
    "inputs": {
      "image": "2636c786c4c0e6c33db28ba14bbe1c381ed4f7cbd8ae925b745e370640e55fea.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "141": {
    "inputs": {
      "max_resolution": 1024,
      "jpeg_quality": 80,
      "suppress_default_preview": True,
      "preview_frames": [
        "131",
        1
      ],
      "preview_fps": 12,
      "tiny_vae": "taeh3.safetensors",
      "model": [
        "178",
        0
      ]
    },
    "class_type": "ModelPreviewOverrideKJ",
    "_meta": {
      "title": "Model Preview Override KJ"
    }
  },
  "147": {
    "inputs": {
      "lora_name": "minimax_h3_ref2v_turbo_8step_v1.0_768p_comfyui_bf16.safetensors",
      "strength_model": 1.0000000000000002,
      "model": [
        "127",
        0
      ]
    },
    "class_type": "LoraLoaderModelOnly",
    "_meta": {
      "title": "Load LoRA"
    }
  },
  "149": {
    "inputs": {
      "shift_video": 12,
      "shift_audio": 3,
      "model": [
        "147",
        0
      ]
    },
    "class_type": "MiniMaxH3SigmaShift",
    "_meta": {
      "title": "ModelSamplingMiniMaxH3"
    }
  },
  "178": {
    "inputs": {
      "attention": "comfy kitchen attention",
      "model": [
        "149",
        0
      ]
    },
    "class_type": "ModelAttentionBackend",
    "_meta": {
      "title": "ModelAttentionBackend"
    }
  },
  "208": {
    "inputs": {
      "step": 6,
      "sigmas": [
        "254",
        0
      ]
    },
    "class_type": "SplitSigmas",
    "_meta": {
      "title": "SplitSigmas"
    }
  },
  "209": {
    "inputs": {
      "noise": [
        "129",
        0
      ],
      "guider": [
        "126",
        0
      ],
      "sampler": [
        "123",
        0
      ],
      "sigmas": [
        "208",
        1
      ],
      "latent_image": [
        "212",
        0
      ]
    },
    "class_type": "SamplerCustomAdvanced",
    "_meta": {
      "title": "SamplerCustomAdvanced"
    }
  },
  "211": {
    "inputs": {
      "av_latent": [
        "125",
        1
      ]
    },
    "class_type": "LTXVSeparateAVLatent",
    "_meta": {
      "title": "Separate AV Latent"
    }
  },
  "212": {
    "inputs": {
      "video_latent": [
        "263",
        0
      ],
      "audio_latent": [
        "211",
        1
      ]
    },
    "class_type": "LTXVConcatAVLatent",
    "_meta": {
      "title": "Concat AV Latent"
    }
  },
  "218": {
    "inputs": {
      "samples": [
        "209",
        0
      ],
      "vae": [
        "120",
        0
      ]
    },
    "class_type": "VAEDecodeAudio",
    "_meta": {
      "title": "VAE Decode Audio"
    }
  },
  "219": {
    "inputs": {
      "samples": [
        "209",
        0
      ],
      "vae": [
        "119",
        0
      ]
    },
    "class_type": "VAEDecode",
    "_meta": {
      "title": "VAE Decode"
    }
  },
  "254": {
    "inputs": {
      "extra_steps": 1,
      "start_at_sigma": 0.7,
      "end_at_sigma": 0,
      "spacing": "cosine",
      "sigmas": [
        "124",
        0
      ]
    },
    "class_type": "H3SigmaRefiner",
    "_meta": {
      "title": "H3 Sigma Refiner"
    }
  },
  "256": {
    "inputs": {
      "image": "07d2e1d22673808899bba100354351b0d4b5b723a10358c7a9ffe92ec0c98ddc.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "257": {
    "inputs": {
      "image": "56a596334282d0057a0847e7a1f2714e8aa27725718b5a162e3ac33c02e42b17.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "258": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "259": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "260": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "263": {
    "inputs": {
      "model_name": "minimax_h3_latent_upscaler_3d_fp16.safetensors",
      "mode": "scale by multiplier",
      "mode.scale": 2,
      "align": 32,
      "device": "cuda",
      "precision": "fp16",
      "enable_chunking": True,
      "latent": [
        "211",
        0
      ]
    },
    "class_type": "MinimaxH3LatentUpscaler3D",
    "_meta": {
      "title": "Minimax H3 Latent Upscaler (3D)"
    }
  },
  "271": {
    "inputs": {
      "frame_rate": 24,
      "loop_count": 0,
      "filename_prefix": "第二次采样",
      "format": "video/h264-mp4",
      "pix_fmt": "yuv420p",
      "crf": 19,
      "save_metadata": True,
      "trim_to_audio": False,
      "pingpong": False,
      "save_output": True,
      "no_preview": False,
      "images": [
        "219",
        0
      ],
      "audio": [
        "218",
        0
      ]
    },
    "class_type": "VHS_VideoCombine",
    "_meta": {
      "title": "Video Combine 🎥🅥🅗🅢"
    }
  },
  "272": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "273": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "274": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "276": {
    "inputs": {
      "video": "1657d341db3688d8d05445f775e8692a0041b27116db8b746fbc5c96a829deb1.mp4",
      "force_rate": 24,
      "force_size": "Disabled",
      "custom_width": 0,
      "custom_height": 0,
      "frame_load_cap": 0,
      "skip_first_frames": 0,
      "select_every_nth": 1,
      "format": "AnimateDiff"
    },
    "class_type": "VHS_LoadVideo",
    "_meta": {
      "title": "Load Video (Upload) 🎥🅥🅗🅢"
    }
  }
}

# minimax_h3 6张图片加上1个参考视频的背景音频
minimax_h3_6_image_1_video_json = {
  "115": {
    "inputs": {
      "aspect_ratio": "16:9 (Widescreen)",
      "megapixels": 0.5,
      "multiple": 32
    },
    "class_type": "ResolutionSelector",
    "_meta": {
      "title": "PASS1 / 16:9 / 0.5MP"
    }
  },
  "119": {
    "inputs": {
      "vae_name": "minimax_h3_video_vae_fp16.safetensors"
    },
    "class_type": "VAELoader",
    "_meta": {
      "title": "Load VAE"
    }
  },
  "120": {
    "inputs": {
      "vae_name": "minimax_h3_audio_vae_fp32.safetensors"
    },
    "class_type": "VAELoader",
    "_meta": {
      "title": "Load VAE"
    }
  },
  "123": {
    "inputs": {
      "sampler_name": "euler"
    },
    "class_type": "KSamplerSelect",
    "_meta": {
      "title": "KSamplerSelect"
    }
  },
  "124": {
    "inputs": {
      "scheduler": "simple",
      "steps": 10,
      "denoise": 1,
      "model": [
        "141",
        0
      ]
    },
    "class_type": "BasicScheduler",
    "_meta": {
      "title": "BasicScheduler"
    }
  },
  "125": {
    "inputs": {
      "noise": [
        "129",
        0
      ],
      "guider": [
        "126",
        0
      ],
      "sampler": [
        "123",
        0
      ],
      "sigmas": [
        "208",
        0
      ],
      "latent_image": [
        "136",
        1
      ]
    },
    "class_type": "SamplerCustomAdvanced",
    "_meta": {
      "title": "SamplerCustomAdvanced"
    }
  },
  "126": {
    "inputs": {
      "model": [
        "141",
        0
      ],
      "conditioning": [
        "136",
        0
      ]
    },
    "class_type": "BasicGuider",
    "_meta": {
      "title": "Basic Guider"
    }
  },
  "127": {
    "inputs": {
      "unet_name": "minimax_h3_hybrid_fl2va_ref2va_b25-49-int8.safetensors",
      "weight_dtype": "default"
    },
    "class_type": "UNETLoader",
    "_meta": {
      "title": "Load Diffusion Model"
    }
  },
  "128": {
    "inputs": {
      "clip_name": "qwen3vl_32b_minimax_h3_int8_convrot.safetensors",
      "type": "minimax",
      "device": "default"
    },
    "class_type": "CLIPLoader",
    "_meta": {
      "title": "Load CLIP"
    }
  },
  "129": {
    "inputs": {
      "noise_seed": 999
    },
    "class_type": "RandomNoise",
    "_meta": {
      "title": "RandomNoise"
    }
  },
  "131": {
    "inputs": {
      "expression": "max(5, round(a * 24)) + (5 - (max(5, round(a * 24)) % 17)) % 17",
      "values.a": [
        "132",
        0
      ]
    },
    "class_type": "ComfyMathExpression",
    "_meta": {
      "title": "Math Expression"
    }
  },
  "132": {
    "inputs": {
      "value": 6
    },
    "class_type": "PrimitiveFloat",
    "_meta": {
      "title": "Float (Duration)"
    }
  },
  "136": {
    "inputs": {
      "prompt": [
        "138",
        0
      ],
      "width": [
        "115",
        0
      ],
      "height": [
        "115",
        1
      ],
      "length": [
        "131",
        1
      ],
      "task_type": "auto",
      "audio_mode": "native",
      "audio_denoise_strength": 1,
      "add_source_as_reference": False,
      "prompt_primary_audio_ordinal": 0,
      "strict_prompt_tags": True,
      "ref_image_size": "match",
      "reference_video_policy": "official_2_to_15s",
      "allow_above_reference_area": True,
      "clip": [
        "128",
        0
      ],
      "video_vae": [
        "119",
        0
      ],
      "audio_vae": [
        "120",
        0
      ],
      "ref_images.ref_image_0": [
        "139",
        0
      ],
      "ref_images.ref_image_1": [
        "256",
        0
      ],
      "ref_images.ref_image_2": [
        "257",
        0
      ],
      "ref_images.ref_image_3": [
        "258",
        0
      ],
      "ref_images.ref_image_4": [
        "259",
        0
      ],
      "ref_images.ref_image_5": [
        "260",
        0
      ],
      "ref_audios.ref_audio_0": [
        "276",
        2
      ]
    },
    "class_type": "MiniMaxH3AudioConditioningT8",
    "_meta": {
      "title": "T8 条件节点｜通用模式"
    }
  },
  "138": {
    "inputs": {
      "value": "subject_definitions:\\n<Subject 1> is Lin Che from <Picture 1>, a 29-year-old Chinese woman with a chin-length black bob, a small mole at the outer end of her left eyebrow, a dark red buttoned knitted cardigan over a white crew-neck top and black trousers. Preserve her facial identity, natural skin and wardrobe; the three standing views do not dictate her seated performance.\\n<Subject 2> is Chen Li from <Picture 2>, a 48-year-old Chinese man with a square face, short black hair graying at the temples, a slight gap in his right eyebrow, a medium-gray knitted cardigan over a pale blue shirt and dark gray trousers. Preserve his face, age, hair and clothing, not the reference pose.\\n<Subject 3> is the same empty meeting room from <Picture 3>: a matte light-gray rectangular table with its long axis east-west, one chair at each east and west short end, a closed high frosted window in the north wall, a low dark-green six-cubby cabinet against the west wall and a closed brown door in the south wall. Preserve the world-space layout and matte surfaces. Omit the four-view borders, reference viewpoints and incidental objects; the room contains only the two directed people and the one directed recorder.\\n\\nsummary:\\n[reference generation] A 6-second continuous live-action medium shot in <Subject 3>. Lin Che establishes that the recorder is already running and challenges Chen Li to speak on record. The three pictures supply identity and room design, with newly directed framing rather than exact endpoints.\\n\\nretention_analysis:\\n<Subject 1> (appears in [Shot 1]): fully_preserved - Keep Lin Che's identity, bob, dark red cardigan and white inner top while directing the specified seated performance.\\n<Subject 2> (appears in [Shot 1]): fully_preserved - Keep Chen Li's identity, gray temples, gray cardigan and pale blue shirt; the directed seated pose replaces the standing reference.\\n<Subject 3> (appears in [Shot 1]): partially_preserved - Keep the fixed room topology, north-window light, west cabinet and table material; omit multi-view panels and reference framing. The initial camera composition is newly directed.\\n\\ndetailed_description:\\nThe target video is a restrained contemporary Chinese live-action suspense drama, with natural skin texture, readable faces and softly lit matte surfaces.\\n[Shot 1] The camera occupies the open southeast aisle at approximately (1.5,-1.5,1.3) meters relative to the table center and faces northwest toward <Subject 1>. She is seated at the west end on screen-left, torso and head turned east toward <Subject 2>, with her gaze going screen-right. Her chin-length bob, natural eyebrow mark and dark red cardigan remain visible. His gray-clad shoulder and pale blue collar occupy only the extreme right foreground; his body remains at the east seat, and his shoulder does not obscure her face, hands or the recorder. The background shows the west green cabinet and only a geometrically plausible part of the north wall and window. The south door stays behind the camera and out of frame.\\nBoth remain seated on the same two chairs, feet on the floor, with neither changing seats or turning away. <Subject 1>'s two empty hands rest separately on the west table edge; <Subject 2>'s left hand rests on the east edge. There is exactly one small black rectangular audio recorder, about 10 by 3 by 1 centimeters, lying flat on the matte tabletop, long axis east-west and its single red indicator steadily lit. It has no readable display. Its center is 0.35 meters east and 0.12 meters south of the table center. His right fingertips rest on the tabletop three centimeters east of the recorder, separated from its casing. The recorder and both hands remain still until any explicitly directed action.\\nHold the initial pose for about one second. <Subject 1> (S1), using a clear low young-adult female Mandarin voice, measured and direct, says <d>[Chinese] 录音开着。你还要我关掉？</d> The statement about recording is a condition of this conversation, not a command to press a button. Finish speaking by about 4.5 seconds, close the mouth and hold eye contact for the remaining beat. Only speech-related lips, small facial tension and natural breathing change. The listener keeps a closed mouth and still hands. No control is pressed, and the indicator remains steadily red.\\nThe sole key is diffused cool-neutral daylight from the fixed high north window, above seated eye level. It softly illuminates the north-facing cheek, the upper knuckles and the recorder's top plane. Weak, slightly warm bounce from the south wall preserves detail on the shadow side without creating another hard shadow. Hair casts a gentle edge at the jaw, and sleeves retain soft folds. Small contact shadows attach hands and the recorder to the tabletop and extend toward the south in world space; the stationary recorder retains a stationary contact shadow. Keep source positions, exposure and white balance steady. Matte surfaces produce subdued highlights rather than flashes. Changing the viewpoint must not relocate the light to the camera side.\\nUse a 40 mm-equivalent lens at seated eye height, in a medium composition with enough depth of field for the featured face, hands and recorder to remain legible. Focus stays on the featured person's eyes without a focus pull. The camera remains fixed throughout; position, orientation, focal length and framing stay unchanged. The foreground shoulder remains a narrow edge element, not a moving wipe or obstruction. Keep the same single shot from beginning to end.\\nThe output is one full-frame scene, with no reference panels, additional people, automatic captions or decorative overlays. Preserve the settled end pose for the adjacent reverse-angle cut.\\n\\noverall_soundscape:\\nLow steady ventilation and distant, muffled room ambience, with subtle breaths and fabric noise. The stationary recorder produces no playback, beeps or repeated scrape. Keep the room tone unobtrusive beneath the voice.\\n\\nnon_diegetic_music:\\nN/A"
    },
    "class_type": "PrimitiveStringMultiline",
    "_meta": {
      "title": "Input Text (Prompt)"
    }
  },
  "139": {
    "inputs": {
      "image": "2636c786c4c0e6c33db28ba14bbe1c381ed4f7cbd8ae925b745e370640e55fea.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "141": {
    "inputs": {
      "max_resolution": 1024,
      "jpeg_quality": 80,
      "suppress_default_preview": True,
      "preview_frames": [
        "131",
        1
      ],
      "preview_fps": 12,
      "tiny_vae": "taeh3.safetensors",
      "model": [
        "178",
        0
      ]
    },
    "class_type": "ModelPreviewOverrideKJ",
    "_meta": {
      "title": "Model Preview Override KJ"
    }
  },
  "147": {
    "inputs": {
      "lora_name": "minimax_h3_ref2v_turbo_8step_v1.0_768p_comfyui_bf16.safetensors",
      "strength_model": 1.0000000000000002,
      "model": [
        "127",
        0
      ]
    },
    "class_type": "LoraLoaderModelOnly",
    "_meta": {
      "title": "Load LoRA"
    }
  },
  "149": {
    "inputs": {
      "shift_video": 12,
      "shift_audio": 3,
      "model": [
        "147",
        0
      ]
    },
    "class_type": "MiniMaxH3SigmaShift",
    "_meta": {
      "title": "ModelSamplingMiniMaxH3"
    }
  },
  "178": {
    "inputs": {
      "attention": "comfy kitchen attention",
      "model": [
        "149",
        0
      ]
    },
    "class_type": "ModelAttentionBackend",
    "_meta": {
      "title": "ModelAttentionBackend"
    }
  },
  "208": {
    "inputs": {
      "step": 6,
      "sigmas": [
        "254",
        0
      ]
    },
    "class_type": "SplitSigmas",
    "_meta": {
      "title": "SplitSigmas"
    }
  },
  "209": {
    "inputs": {
      "noise": [
        "129",
        0
      ],
      "guider": [
        "126",
        0
      ],
      "sampler": [
        "123",
        0
      ],
      "sigmas": [
        "208",
        1
      ],
      "latent_image": [
        "212",
        0
      ]
    },
    "class_type": "SamplerCustomAdvanced",
    "_meta": {
      "title": "SamplerCustomAdvanced"
    }
  },
  "211": {
    "inputs": {
      "av_latent": [
        "125",
        1
      ]
    },
    "class_type": "LTXVSeparateAVLatent",
    "_meta": {
      "title": "Separate AV Latent"
    }
  },
  "212": {
    "inputs": {
      "video_latent": [
        "263",
        0
      ],
      "audio_latent": [
        "211",
        1
      ]
    },
    "class_type": "LTXVConcatAVLatent",
    "_meta": {
      "title": "Concat AV Latent"
    }
  },
  "218": {
    "inputs": {
      "samples": [
        "209",
        0
      ],
      "vae": [
        "120",
        0
      ]
    },
    "class_type": "VAEDecodeAudio",
    "_meta": {
      "title": "VAE Decode Audio"
    }
  },
  "219": {
    "inputs": {
      "samples": [
        "209",
        0
      ],
      "vae": [
        "119",
        0
      ]
    },
    "class_type": "VAEDecode",
    "_meta": {
      "title": "VAE Decode"
    }
  },
  "254": {
    "inputs": {
      "extra_steps": 1,
      "start_at_sigma": 0.7,
      "end_at_sigma": 0,
      "spacing": "cosine",
      "sigmas": [
        "124",
        0
      ]
    },
    "class_type": "H3SigmaRefiner",
    "_meta": {
      "title": "H3 Sigma Refiner"
    }
  },
  "256": {
    "inputs": {
      "image": "07d2e1d22673808899bba100354351b0d4b5b723a10358c7a9ffe92ec0c98ddc.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "257": {
    "inputs": {
      "image": "56a596334282d0057a0847e7a1f2714e8aa27725718b5a162e3ac33c02e42b17.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "258": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "259": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "260": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "263": {
    "inputs": {
      "model_name": "minimax_h3_latent_upscaler_3d_fp16.safetensors",
      "mode": "scale by multiplier",
      "mode.scale": 2,
      "align": 32,
      "device": "cuda",
      "precision": "fp16",
      "enable_chunking": True,
      "latent": [
        "211",
        0
      ]
    },
    "class_type": "MinimaxH3LatentUpscaler3D",
    "_meta": {
      "title": "Minimax H3 Latent Upscaler (3D)"
    }
  },
  "271": {
    "inputs": {
      "frame_rate": 24,
      "loop_count": 0,
      "filename_prefix": "第二次采样",
      "format": "video/h264-mp4",
      "pix_fmt": "yuv420p",
      "crf": 19,
      "save_metadata": True,
      "trim_to_audio": False,
      "pingpong": False,
      "save_output": True,
      "no_preview": False,
      "images": [
        "219",
        0
      ],
      "audio": [
        "218",
        0
      ]
    },
    "class_type": "VHS_VideoCombine",
    "_meta": {
      "title": "Video Combine 🎥🅥🅗🅢"
    }
  },
  "272": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "273": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "274": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "276": {
    "inputs": {
      "video": "1657d341db3688d8d05445f775e8692a0041b27116db8b746fbc5c96a829deb1.mp4",
      "force_rate": 24,
      "force_size": "Disabled",
      "custom_width": 0,
      "custom_height": 0,
      "frame_load_cap": 0,
      "skip_first_frames": 0,
      "select_every_nth": 1,
      "format": "AnimateDiff"
    },
    "class_type": "VHS_LoadVideo",
    "_meta": {
      "title": "Load Video (Upload) 🎥🅥🅗🅢"
    }
  }
}

# minimax_h3 5张图片加上1个参考视频的背景音频
minimax_h3_5_image_1_video_json = {
  "115": {
    "inputs": {
      "aspect_ratio": "16:9 (Widescreen)",
      "megapixels": 0.5,
      "multiple": 32
    },
    "class_type": "ResolutionSelector",
    "_meta": {
      "title": "PASS1 / 16:9 / 0.5MP"
    }
  },
  "119": {
    "inputs": {
      "vae_name": "minimax_h3_video_vae_fp16.safetensors"
    },
    "class_type": "VAELoader",
    "_meta": {
      "title": "Load VAE"
    }
  },
  "120": {
    "inputs": {
      "vae_name": "minimax_h3_audio_vae_fp32.safetensors"
    },
    "class_type": "VAELoader",
    "_meta": {
      "title": "Load VAE"
    }
  },
  "123": {
    "inputs": {
      "sampler_name": "euler"
    },
    "class_type": "KSamplerSelect",
    "_meta": {
      "title": "KSamplerSelect"
    }
  },
  "124": {
    "inputs": {
      "scheduler": "simple",
      "steps": 10,
      "denoise": 1,
      "model": [
        "141",
        0
      ]
    },
    "class_type": "BasicScheduler",
    "_meta": {
      "title": "BasicScheduler"
    }
  },
  "125": {
    "inputs": {
      "noise": [
        "129",
        0
      ],
      "guider": [
        "126",
        0
      ],
      "sampler": [
        "123",
        0
      ],
      "sigmas": [
        "208",
        0
      ],
      "latent_image": [
        "136",
        1
      ]
    },
    "class_type": "SamplerCustomAdvanced",
    "_meta": {
      "title": "SamplerCustomAdvanced"
    }
  },
  "126": {
    "inputs": {
      "model": [
        "141",
        0
      ],
      "conditioning": [
        "136",
        0
      ]
    },
    "class_type": "BasicGuider",
    "_meta": {
      "title": "Basic Guider"
    }
  },
  "127": {
    "inputs": {
      "unet_name": "minimax_h3_hybrid_fl2va_ref2va_b25-49-int8.safetensors",
      "weight_dtype": "default"
    },
    "class_type": "UNETLoader",
    "_meta": {
      "title": "Load Diffusion Model"
    }
  },
  "128": {
    "inputs": {
      "clip_name": "qwen3vl_32b_minimax_h3_int8_convrot.safetensors",
      "type": "minimax",
      "device": "default"
    },
    "class_type": "CLIPLoader",
    "_meta": {
      "title": "Load CLIP"
    }
  },
  "129": {
    "inputs": {
      "noise_seed": 999
    },
    "class_type": "RandomNoise",
    "_meta": {
      "title": "RandomNoise"
    }
  },
  "131": {
    "inputs": {
      "expression": "max(5, round(a * 24)) + (5 - (max(5, round(a * 24)) % 17)) % 17",
      "values.a": [
        "132",
        0
      ]
    },
    "class_type": "ComfyMathExpression",
    "_meta": {
      "title": "Math Expression"
    }
  },
  "132": {
    "inputs": {
      "value": 6
    },
    "class_type": "PrimitiveFloat",
    "_meta": {
      "title": "Float (Duration)"
    }
  },
  "136": {
    "inputs": {
      "prompt": [
        "138",
        0
      ],
      "width": [
        "115",
        0
      ],
      "height": [
        "115",
        1
      ],
      "length": [
        "131",
        1
      ],
      "task_type": "auto",
      "audio_mode": "native",
      "audio_denoise_strength": 1,
      "add_source_as_reference": False,
      "prompt_primary_audio_ordinal": 0,
      "strict_prompt_tags": True,
      "ref_image_size": "match",
      "reference_video_policy": "official_2_to_15s",
      "allow_above_reference_area": True,
      "clip": [
        "128",
        0
      ],
      "video_vae": [
        "119",
        0
      ],
      "audio_vae": [
        "120",
        0
      ],
      "ref_images.ref_image_0": [
        "139",
        0
      ],
      "ref_images.ref_image_1": [
        "256",
        0
      ],
      "ref_images.ref_image_2": [
        "257",
        0
      ],
      "ref_images.ref_image_3": [
        "258",
        0
      ],
      "ref_images.ref_image_4": [
        "259",
        0
      ],
      "ref_audios.ref_audio_0": [
        "276",
        2
      ]
    },
    "class_type": "MiniMaxH3AudioConditioningT8",
    "_meta": {
      "title": "T8 条件节点｜通用模式"
    }
  },
  "138": {
    "inputs": {
      "value": "subject_definitions:\\n<Subject 1> is Lin Che from <Picture 1>, a 29-year-old Chinese woman with a chin-length black bob, a small mole at the outer end of her left eyebrow, a dark red buttoned knitted cardigan over a white crew-neck top and black trousers. Preserve her facial identity, natural skin and wardrobe; the three standing views do not dictate her seated performance.\\n<Subject 2> is Chen Li from <Picture 2>, a 48-year-old Chinese man with a square face, short black hair graying at the temples, a slight gap in his right eyebrow, a medium-gray knitted cardigan over a pale blue shirt and dark gray trousers. Preserve his face, age, hair and clothing, not the reference pose.\\n<Subject 3> is the same empty meeting room from <Picture 3>: a matte light-gray rectangular table with its long axis east-west, one chair at each east and west short end, a closed high frosted window in the north wall, a low dark-green six-cubby cabinet against the west wall and a closed brown door in the south wall. Preserve the world-space layout and matte surfaces. Omit the four-view borders, reference viewpoints and incidental objects; the room contains only the two directed people and the one directed recorder.\\n\\nsummary:\\n[reference generation] A 6-second continuous live-action medium shot in <Subject 3>. Lin Che establishes that the recorder is already running and challenges Chen Li to speak on record. The three pictures supply identity and room design, with newly directed framing rather than exact endpoints.\\n\\nretention_analysis:\\n<Subject 1> (appears in [Shot 1]): fully_preserved - Keep Lin Che's identity, bob, dark red cardigan and white inner top while directing the specified seated performance.\\n<Subject 2> (appears in [Shot 1]): fully_preserved - Keep Chen Li's identity, gray temples, gray cardigan and pale blue shirt; the directed seated pose replaces the standing reference.\\n<Subject 3> (appears in [Shot 1]): partially_preserved - Keep the fixed room topology, north-window light, west cabinet and table material; omit multi-view panels and reference framing. The initial camera composition is newly directed.\\n\\ndetailed_description:\\nThe target video is a restrained contemporary Chinese live-action suspense drama, with natural skin texture, readable faces and softly lit matte surfaces.\\n[Shot 1] The camera occupies the open southeast aisle at approximately (1.5,-1.5,1.3) meters relative to the table center and faces northwest toward <Subject 1>. She is seated at the west end on screen-left, torso and head turned east toward <Subject 2>, with her gaze going screen-right. Her chin-length bob, natural eyebrow mark and dark red cardigan remain visible. His gray-clad shoulder and pale blue collar occupy only the extreme right foreground; his body remains at the east seat, and his shoulder does not obscure her face, hands or the recorder. The background shows the west green cabinet and only a geometrically plausible part of the north wall and window. The south door stays behind the camera and out of frame.\\nBoth remain seated on the same two chairs, feet on the floor, with neither changing seats or turning away. <Subject 1>'s two empty hands rest separately on the west table edge; <Subject 2>'s left hand rests on the east edge. There is exactly one small black rectangular audio recorder, about 10 by 3 by 1 centimeters, lying flat on the matte tabletop, long axis east-west and its single red indicator steadily lit. It has no readable display. Its center is 0.35 meters east and 0.12 meters south of the table center. His right fingertips rest on the tabletop three centimeters east of the recorder, separated from its casing. The recorder and both hands remain still until any explicitly directed action.\\nHold the initial pose for about one second. <Subject 1> (S1), using a clear low young-adult female Mandarin voice, measured and direct, says <d>[Chinese] 录音开着。你还要我关掉？</d> The statement about recording is a condition of this conversation, not a command to press a button. Finish speaking by about 4.5 seconds, close the mouth and hold eye contact for the remaining beat. Only speech-related lips, small facial tension and natural breathing change. The listener keeps a closed mouth and still hands. No control is pressed, and the indicator remains steadily red.\\nThe sole key is diffused cool-neutral daylight from the fixed high north window, above seated eye level. It softly illuminates the north-facing cheek, the upper knuckles and the recorder's top plane. Weak, slightly warm bounce from the south wall preserves detail on the shadow side without creating another hard shadow. Hair casts a gentle edge at the jaw, and sleeves retain soft folds. Small contact shadows attach hands and the recorder to the tabletop and extend toward the south in world space; the stationary recorder retains a stationary contact shadow. Keep source positions, exposure and white balance steady. Matte surfaces produce subdued highlights rather than flashes. Changing the viewpoint must not relocate the light to the camera side.\\nUse a 40 mm-equivalent lens at seated eye height, in a medium composition with enough depth of field for the featured face, hands and recorder to remain legible. Focus stays on the featured person's eyes without a focus pull. The camera remains fixed throughout; position, orientation, focal length and framing stay unchanged. The foreground shoulder remains a narrow edge element, not a moving wipe or obstruction. Keep the same single shot from beginning to end.\\nThe output is one full-frame scene, with no reference panels, additional people, automatic captions or decorative overlays. Preserve the settled end pose for the adjacent reverse-angle cut.\\n\\noverall_soundscape:\\nLow steady ventilation and distant, muffled room ambience, with subtle breaths and fabric noise. The stationary recorder produces no playback, beeps or repeated scrape. Keep the room tone unobtrusive beneath the voice.\\n\\nnon_diegetic_music:\\nN/A"
    },
    "class_type": "PrimitiveStringMultiline",
    "_meta": {
      "title": "Input Text (Prompt)"
    }
  },
  "139": {
    "inputs": {
      "image": "2636c786c4c0e6c33db28ba14bbe1c381ed4f7cbd8ae925b745e370640e55fea.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "141": {
    "inputs": {
      "max_resolution": 1024,
      "jpeg_quality": 80,
      "suppress_default_preview": True,
      "preview_frames": [
        "131",
        1
      ],
      "preview_fps": 12,
      "tiny_vae": "taeh3.safetensors",
      "model": [
        "178",
        0
      ]
    },
    "class_type": "ModelPreviewOverrideKJ",
    "_meta": {
      "title": "Model Preview Override KJ"
    }
  },
  "147": {
    "inputs": {
      "lora_name": "minimax_h3_ref2v_turbo_8step_v1.0_768p_comfyui_bf16.safetensors",
      "strength_model": 1.0000000000000002,
      "model": [
        "127",
        0
      ]
    },
    "class_type": "LoraLoaderModelOnly",
    "_meta": {
      "title": "Load LoRA"
    }
  },
  "149": {
    "inputs": {
      "shift_video": 12,
      "shift_audio": 3,
      "model": [
        "147",
        0
      ]
    },
    "class_type": "MiniMaxH3SigmaShift",
    "_meta": {
      "title": "ModelSamplingMiniMaxH3"
    }
  },
  "178": {
    "inputs": {
      "attention": "comfy kitchen attention",
      "model": [
        "149",
        0
      ]
    },
    "class_type": "ModelAttentionBackend",
    "_meta": {
      "title": "ModelAttentionBackend"
    }
  },
  "208": {
    "inputs": {
      "step": 6,
      "sigmas": [
        "254",
        0
      ]
    },
    "class_type": "SplitSigmas",
    "_meta": {
      "title": "SplitSigmas"
    }
  },
  "209": {
    "inputs": {
      "noise": [
        "129",
        0
      ],
      "guider": [
        "126",
        0
      ],
      "sampler": [
        "123",
        0
      ],
      "sigmas": [
        "208",
        1
      ],
      "latent_image": [
        "212",
        0
      ]
    },
    "class_type": "SamplerCustomAdvanced",
    "_meta": {
      "title": "SamplerCustomAdvanced"
    }
  },
  "211": {
    "inputs": {
      "av_latent": [
        "125",
        1
      ]
    },
    "class_type": "LTXVSeparateAVLatent",
    "_meta": {
      "title": "Separate AV Latent"
    }
  },
  "212": {
    "inputs": {
      "video_latent": [
        "263",
        0
      ],
      "audio_latent": [
        "211",
        1
      ]
    },
    "class_type": "LTXVConcatAVLatent",
    "_meta": {
      "title": "Concat AV Latent"
    }
  },
  "218": {
    "inputs": {
      "samples": [
        "209",
        0
      ],
      "vae": [
        "120",
        0
      ]
    },
    "class_type": "VAEDecodeAudio",
    "_meta": {
      "title": "VAE Decode Audio"
    }
  },
  "219": {
    "inputs": {
      "samples": [
        "209",
        0
      ],
      "vae": [
        "119",
        0
      ]
    },
    "class_type": "VAEDecode",
    "_meta": {
      "title": "VAE Decode"
    }
  },
  "254": {
    "inputs": {
      "extra_steps": 1,
      "start_at_sigma": 0.7,
      "end_at_sigma": 0,
      "spacing": "cosine",
      "sigmas": [
        "124",
        0
      ]
    },
    "class_type": "H3SigmaRefiner",
    "_meta": {
      "title": "H3 Sigma Refiner"
    }
  },
  "256": {
    "inputs": {
      "image": "07d2e1d22673808899bba100354351b0d4b5b723a10358c7a9ffe92ec0c98ddc.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "257": {
    "inputs": {
      "image": "56a596334282d0057a0847e7a1f2714e8aa27725718b5a162e3ac33c02e42b17.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "258": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "259": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "260": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "263": {
    "inputs": {
      "model_name": "minimax_h3_latent_upscaler_3d_fp16.safetensors",
      "mode": "scale by multiplier",
      "mode.scale": 2,
      "align": 32,
      "device": "cuda",
      "precision": "fp16",
      "enable_chunking": True,
      "latent": [
        "211",
        0
      ]
    },
    "class_type": "MinimaxH3LatentUpscaler3D",
    "_meta": {
      "title": "Minimax H3 Latent Upscaler (3D)"
    }
  },
  "271": {
    "inputs": {
      "frame_rate": 24,
      "loop_count": 0,
      "filename_prefix": "第二次采样",
      "format": "video/h264-mp4",
      "pix_fmt": "yuv420p",
      "crf": 19,
      "save_metadata": True,
      "trim_to_audio": False,
      "pingpong": False,
      "save_output": True,
      "no_preview": False,
      "images": [
        "219",
        0
      ],
      "audio": [
        "218",
        0
      ]
    },
    "class_type": "VHS_VideoCombine",
    "_meta": {
      "title": "Video Combine 🎥🅥🅗🅢"
    }
  },
  "272": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "273": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "274": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "276": {
    "inputs": {
      "video": "1657d341db3688d8d05445f775e8692a0041b27116db8b746fbc5c96a829deb1.mp4",
      "force_rate": 24,
      "force_size": "Disabled",
      "custom_width": 0,
      "custom_height": 0,
      "frame_load_cap": 0,
      "skip_first_frames": 0,
      "select_every_nth": 1,
      "format": "AnimateDiff"
    },
    "class_type": "VHS_LoadVideo",
    "_meta": {
      "title": "Load Video (Upload) 🎥🅥🅗🅢"
    }
  }
}

# minimax_h3 4张图片加上1个参考视频的背景音频
minimax_h3_4_image_1_video_json = {
  "115": {
    "inputs": {
      "aspect_ratio": "16:9 (Widescreen)",
      "megapixels": 0.5,
      "multiple": 32
    },
    "class_type": "ResolutionSelector",
    "_meta": {
      "title": "PASS1 / 16:9 / 0.5MP"
    }
  },
  "119": {
    "inputs": {
      "vae_name": "minimax_h3_video_vae_fp16.safetensors"
    },
    "class_type": "VAELoader",
    "_meta": {
      "title": "Load VAE"
    }
  },
  "120": {
    "inputs": {
      "vae_name": "minimax_h3_audio_vae_fp32.safetensors"
    },
    "class_type": "VAELoader",
    "_meta": {
      "title": "Load VAE"
    }
  },
  "123": {
    "inputs": {
      "sampler_name": "euler"
    },
    "class_type": "KSamplerSelect",
    "_meta": {
      "title": "KSamplerSelect"
    }
  },
  "124": {
    "inputs": {
      "scheduler": "simple",
      "steps": 10,
      "denoise": 1,
      "model": [
        "141",
        0
      ]
    },
    "class_type": "BasicScheduler",
    "_meta": {
      "title": "BasicScheduler"
    }
  },
  "125": {
    "inputs": {
      "noise": [
        "129",
        0
      ],
      "guider": [
        "126",
        0
      ],
      "sampler": [
        "123",
        0
      ],
      "sigmas": [
        "208",
        0
      ],
      "latent_image": [
        "136",
        1
      ]
    },
    "class_type": "SamplerCustomAdvanced",
    "_meta": {
      "title": "SamplerCustomAdvanced"
    }
  },
  "126": {
    "inputs": {
      "model": [
        "141",
        0
      ],
      "conditioning": [
        "136",
        0
      ]
    },
    "class_type": "BasicGuider",
    "_meta": {
      "title": "Basic Guider"
    }
  },
  "127": {
    "inputs": {
      "unet_name": "minimax_h3_hybrid_fl2va_ref2va_b25-49-int8.safetensors",
      "weight_dtype": "default"
    },
    "class_type": "UNETLoader",
    "_meta": {
      "title": "Load Diffusion Model"
    }
  },
  "128": {
    "inputs": {
      "clip_name": "qwen3vl_32b_minimax_h3_int8_convrot.safetensors",
      "type": "minimax",
      "device": "default"
    },
    "class_type": "CLIPLoader",
    "_meta": {
      "title": "Load CLIP"
    }
  },
  "129": {
    "inputs": {
      "noise_seed": 999
    },
    "class_type": "RandomNoise",
    "_meta": {
      "title": "RandomNoise"
    }
  },
  "131": {
    "inputs": {
      "expression": "max(5, round(a * 24)) + (5 - (max(5, round(a * 24)) % 17)) % 17",
      "values.a": [
        "132",
        0
      ]
    },
    "class_type": "ComfyMathExpression",
    "_meta": {
      "title": "Math Expression"
    }
  },
  "132": {
    "inputs": {
      "value": 6
    },
    "class_type": "PrimitiveFloat",
    "_meta": {
      "title": "Float (Duration)"
    }
  },
  "136": {
    "inputs": {
      "prompt": [
        "138",
        0
      ],
      "width": [
        "115",
        0
      ],
      "height": [
        "115",
        1
      ],
      "length": [
        "131",
        1
      ],
      "task_type": "auto",
      "audio_mode": "native",
      "audio_denoise_strength": 1,
      "add_source_as_reference": False,
      "prompt_primary_audio_ordinal": 0,
      "strict_prompt_tags": True,
      "ref_image_size": "match",
      "reference_video_policy": "official_2_to_15s",
      "allow_above_reference_area": True,
      "clip": [
        "128",
        0
      ],
      "video_vae": [
        "119",
        0
      ],
      "audio_vae": [
        "120",
        0
      ],
      "ref_images.ref_image_0": [
        "139",
        0
      ],
      "ref_images.ref_image_1": [
        "256",
        0
      ],
      "ref_images.ref_image_2": [
        "257",
        0
      ],
      "ref_images.ref_image_3": [
        "258",
        0
      ],
      "ref_audios.ref_audio_0": [
        "276",
        2
      ]
    },
    "class_type": "MiniMaxH3AudioConditioningT8",
    "_meta": {
      "title": "T8 条件节点｜通用模式"
    }
  },
  "138": {
    "inputs": {
      "value": "subject_definitions:\\n<Subject 1> is Lin Che from <Picture 1>, a 29-year-old Chinese woman with a chin-length black bob, a small mole at the outer end of her left eyebrow, a dark red buttoned knitted cardigan over a white crew-neck top and black trousers. Preserve her facial identity, natural skin and wardrobe; the three standing views do not dictate her seated performance.\\n<Subject 2> is Chen Li from <Picture 2>, a 48-year-old Chinese man with a square face, short black hair graying at the temples, a slight gap in his right eyebrow, a medium-gray knitted cardigan over a pale blue shirt and dark gray trousers. Preserve his face, age, hair and clothing, not the reference pose.\\n<Subject 3> is the same empty meeting room from <Picture 3>: a matte light-gray rectangular table with its long axis east-west, one chair at each east and west short end, a closed high frosted window in the north wall, a low dark-green six-cubby cabinet against the west wall and a closed brown door in the south wall. Preserve the world-space layout and matte surfaces. Omit the four-view borders, reference viewpoints and incidental objects; the room contains only the two directed people and the one directed recorder.\\n\\nsummary:\\n[reference generation] A 6-second continuous live-action medium shot in <Subject 3>. Lin Che establishes that the recorder is already running and challenges Chen Li to speak on record. The three pictures supply identity and room design, with newly directed framing rather than exact endpoints.\\n\\nretention_analysis:\\n<Subject 1> (appears in [Shot 1]): fully_preserved - Keep Lin Che's identity, bob, dark red cardigan and white inner top while directing the specified seated performance.\\n<Subject 2> (appears in [Shot 1]): fully_preserved - Keep Chen Li's identity, gray temples, gray cardigan and pale blue shirt; the directed seated pose replaces the standing reference.\\n<Subject 3> (appears in [Shot 1]): partially_preserved - Keep the fixed room topology, north-window light, west cabinet and table material; omit multi-view panels and reference framing. The initial camera composition is newly directed.\\n\\ndetailed_description:\\nThe target video is a restrained contemporary Chinese live-action suspense drama, with natural skin texture, readable faces and softly lit matte surfaces.\\n[Shot 1] The camera occupies the open southeast aisle at approximately (1.5,-1.5,1.3) meters relative to the table center and faces northwest toward <Subject 1>. She is seated at the west end on screen-left, torso and head turned east toward <Subject 2>, with her gaze going screen-right. Her chin-length bob, natural eyebrow mark and dark red cardigan remain visible. His gray-clad shoulder and pale blue collar occupy only the extreme right foreground; his body remains at the east seat, and his shoulder does not obscure her face, hands or the recorder. The background shows the west green cabinet and only a geometrically plausible part of the north wall and window. The south door stays behind the camera and out of frame.\\nBoth remain seated on the same two chairs, feet on the floor, with neither changing seats or turning away. <Subject 1>'s two empty hands rest separately on the west table edge; <Subject 2>'s left hand rests on the east edge. There is exactly one small black rectangular audio recorder, about 10 by 3 by 1 centimeters, lying flat on the matte tabletop, long axis east-west and its single red indicator steadily lit. It has no readable display. Its center is 0.35 meters east and 0.12 meters south of the table center. His right fingertips rest on the tabletop three centimeters east of the recorder, separated from its casing. The recorder and both hands remain still until any explicitly directed action.\\nHold the initial pose for about one second. <Subject 1> (S1), using a clear low young-adult female Mandarin voice, measured and direct, says <d>[Chinese] 录音开着。你还要我关掉？</d> The statement about recording is a condition of this conversation, not a command to press a button. Finish speaking by about 4.5 seconds, close the mouth and hold eye contact for the remaining beat. Only speech-related lips, small facial tension and natural breathing change. The listener keeps a closed mouth and still hands. No control is pressed, and the indicator remains steadily red.\\nThe sole key is diffused cool-neutral daylight from the fixed high north window, above seated eye level. It softly illuminates the north-facing cheek, the upper knuckles and the recorder's top plane. Weak, slightly warm bounce from the south wall preserves detail on the shadow side without creating another hard shadow. Hair casts a gentle edge at the jaw, and sleeves retain soft folds. Small contact shadows attach hands and the recorder to the tabletop and extend toward the south in world space; the stationary recorder retains a stationary contact shadow. Keep source positions, exposure and white balance steady. Matte surfaces produce subdued highlights rather than flashes. Changing the viewpoint must not relocate the light to the camera side.\\nUse a 40 mm-equivalent lens at seated eye height, in a medium composition with enough depth of field for the featured face, hands and recorder to remain legible. Focus stays on the featured person's eyes without a focus pull. The camera remains fixed throughout; position, orientation, focal length and framing stay unchanged. The foreground shoulder remains a narrow edge element, not a moving wipe or obstruction. Keep the same single shot from beginning to end.\\nThe output is one full-frame scene, with no reference panels, additional people, automatic captions or decorative overlays. Preserve the settled end pose for the adjacent reverse-angle cut.\\n\\noverall_soundscape:\\nLow steady ventilation and distant, muffled room ambience, with subtle breaths and fabric noise. The stationary recorder produces no playback, beeps or repeated scrape. Keep the room tone unobtrusive beneath the voice.\\n\\nnon_diegetic_music:\\nN/A"
    },
    "class_type": "PrimitiveStringMultiline",
    "_meta": {
      "title": "Input Text (Prompt)"
    }
  },
  "139": {
    "inputs": {
      "image": "2636c786c4c0e6c33db28ba14bbe1c381ed4f7cbd8ae925b745e370640e55fea.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "141": {
    "inputs": {
      "max_resolution": 1024,
      "jpeg_quality": 80,
      "suppress_default_preview": True,
      "preview_frames": [
        "131",
        1
      ],
      "preview_fps": 12,
      "tiny_vae": "taeh3.safetensors",
      "model": [
        "178",
        0
      ]
    },
    "class_type": "ModelPreviewOverrideKJ",
    "_meta": {
      "title": "Model Preview Override KJ"
    }
  },
  "147": {
    "inputs": {
      "lora_name": "minimax_h3_ref2v_turbo_8step_v1.0_768p_comfyui_bf16.safetensors",
      "strength_model": 1.0000000000000002,
      "model": [
        "127",
        0
      ]
    },
    "class_type": "LoraLoaderModelOnly",
    "_meta": {
      "title": "Load LoRA"
    }
  },
  "149": {
    "inputs": {
      "shift_video": 12,
      "shift_audio": 3,
      "model": [
        "147",
        0
      ]
    },
    "class_type": "MiniMaxH3SigmaShift",
    "_meta": {
      "title": "ModelSamplingMiniMaxH3"
    }
  },
  "178": {
    "inputs": {
      "attention": "comfy kitchen attention",
      "model": [
        "149",
        0
      ]
    },
    "class_type": "ModelAttentionBackend",
    "_meta": {
      "title": "ModelAttentionBackend"
    }
  },
  "208": {
    "inputs": {
      "step": 6,
      "sigmas": [
        "254",
        0
      ]
    },
    "class_type": "SplitSigmas",
    "_meta": {
      "title": "SplitSigmas"
    }
  },
  "209": {
    "inputs": {
      "noise": [
        "129",
        0
      ],
      "guider": [
        "126",
        0
      ],
      "sampler": [
        "123",
        0
      ],
      "sigmas": [
        "208",
        1
      ],
      "latent_image": [
        "212",
        0
      ]
    },
    "class_type": "SamplerCustomAdvanced",
    "_meta": {
      "title": "SamplerCustomAdvanced"
    }
  },
  "211": {
    "inputs": {
      "av_latent": [
        "125",
        1
      ]
    },
    "class_type": "LTXVSeparateAVLatent",
    "_meta": {
      "title": "Separate AV Latent"
    }
  },
  "212": {
    "inputs": {
      "video_latent": [
        "263",
        0
      ],
      "audio_latent": [
        "211",
        1
      ]
    },
    "class_type": "LTXVConcatAVLatent",
    "_meta": {
      "title": "Concat AV Latent"
    }
  },
  "218": {
    "inputs": {
      "samples": [
        "209",
        0
      ],
      "vae": [
        "120",
        0
      ]
    },
    "class_type": "VAEDecodeAudio",
    "_meta": {
      "title": "VAE Decode Audio"
    }
  },
  "219": {
    "inputs": {
      "samples": [
        "209",
        0
      ],
      "vae": [
        "119",
        0
      ]
    },
    "class_type": "VAEDecode",
    "_meta": {
      "title": "VAE Decode"
    }
  },
  "254": {
    "inputs": {
      "extra_steps": 1,
      "start_at_sigma": 0.7,
      "end_at_sigma": 0,
      "spacing": "cosine",
      "sigmas": [
        "124",
        0
      ]
    },
    "class_type": "H3SigmaRefiner",
    "_meta": {
      "title": "H3 Sigma Refiner"
    }
  },
  "256": {
    "inputs": {
      "image": "07d2e1d22673808899bba100354351b0d4b5b723a10358c7a9ffe92ec0c98ddc.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "257": {
    "inputs": {
      "image": "56a596334282d0057a0847e7a1f2714e8aa27725718b5a162e3ac33c02e42b17.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "258": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "259": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "260": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "263": {
    "inputs": {
      "model_name": "minimax_h3_latent_upscaler_3d_fp16.safetensors",
      "mode": "scale by multiplier",
      "mode.scale": 2,
      "align": 32,
      "device": "cuda",
      "precision": "fp16",
      "enable_chunking": True,
      "latent": [
        "211",
        0
      ]
    },
    "class_type": "MinimaxH3LatentUpscaler3D",
    "_meta": {
      "title": "Minimax H3 Latent Upscaler (3D)"
    }
  },
  "271": {
    "inputs": {
      "frame_rate": 24,
      "loop_count": 0,
      "filename_prefix": "第二次采样",
      "format": "video/h264-mp4",
      "pix_fmt": "yuv420p",
      "crf": 19,
      "save_metadata": True,
      "trim_to_audio": False,
      "pingpong": False,
      "save_output": True,
      "no_preview": False,
      "images": [
        "219",
        0
      ],
      "audio": [
        "218",
        0
      ]
    },
    "class_type": "VHS_VideoCombine",
    "_meta": {
      "title": "Video Combine 🎥🅥🅗🅢"
    }
  },
  "272": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "273": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "274": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "276": {
    "inputs": {
      "video": "1657d341db3688d8d05445f775e8692a0041b27116db8b746fbc5c96a829deb1.mp4",
      "force_rate": 24,
      "force_size": "Disabled",
      "custom_width": 0,
      "custom_height": 0,
      "frame_load_cap": 0,
      "skip_first_frames": 0,
      "select_every_nth": 1,
      "format": "AnimateDiff"
    },
    "class_type": "VHS_LoadVideo",
    "_meta": {
      "title": "Load Video (Upload) 🎥🅥🅗🅢"
    }
  }
}

# minimax_h3 3张图片加上1个参考视频的背景音频
minimax_h3_3_image_1_video_json = {
  "115": {
    "inputs": {
      "aspect_ratio": "16:9 (Widescreen)",
      "megapixels": 0.5,
      "multiple": 32
    },
    "class_type": "ResolutionSelector",
    "_meta": {
      "title": "PASS1 / 16:9 / 0.5MP"
    }
  },
  "119": {
    "inputs": {
      "vae_name": "minimax_h3_video_vae_fp16.safetensors"
    },
    "class_type": "VAELoader",
    "_meta": {
      "title": "Load VAE"
    }
  },
  "120": {
    "inputs": {
      "vae_name": "minimax_h3_audio_vae_fp32.safetensors"
    },
    "class_type": "VAELoader",
    "_meta": {
      "title": "Load VAE"
    }
  },
  "123": {
    "inputs": {
      "sampler_name": "euler"
    },
    "class_type": "KSamplerSelect",
    "_meta": {
      "title": "KSamplerSelect"
    }
  },
  "124": {
    "inputs": {
      "scheduler": "simple",
      "steps": 10,
      "denoise": 1,
      "model": [
        "141",
        0
      ]
    },
    "class_type": "BasicScheduler",
    "_meta": {
      "title": "BasicScheduler"
    }
  },
  "125": {
    "inputs": {
      "noise": [
        "129",
        0
      ],
      "guider": [
        "126",
        0
      ],
      "sampler": [
        "123",
        0
      ],
      "sigmas": [
        "208",
        0
      ],
      "latent_image": [
        "136",
        1
      ]
    },
    "class_type": "SamplerCustomAdvanced",
    "_meta": {
      "title": "SamplerCustomAdvanced"
    }
  },
  "126": {
    "inputs": {
      "model": [
        "141",
        0
      ],
      "conditioning": [
        "136",
        0
      ]
    },
    "class_type": "BasicGuider",
    "_meta": {
      "title": "Basic Guider"
    }
  },
  "127": {
    "inputs": {
      "unet_name": "minimax_h3_hybrid_fl2va_ref2va_b25-49-int8.safetensors",
      "weight_dtype": "default"
    },
    "class_type": "UNETLoader",
    "_meta": {
      "title": "Load Diffusion Model"
    }
  },
  "128": {
    "inputs": {
      "clip_name": "qwen3vl_32b_minimax_h3_int8_convrot.safetensors",
      "type": "minimax",
      "device": "default"
    },
    "class_type": "CLIPLoader",
    "_meta": {
      "title": "Load CLIP"
    }
  },
  "129": {
    "inputs": {
      "noise_seed": 999
    },
    "class_type": "RandomNoise",
    "_meta": {
      "title": "RandomNoise"
    }
  },
  "131": {
    "inputs": {
      "expression": "max(5, round(a * 24)) + (5 - (max(5, round(a * 24)) % 17)) % 17",
      "values.a": [
        "132",
        0
      ]
    },
    "class_type": "ComfyMathExpression",
    "_meta": {
      "title": "Math Expression"
    }
  },
  "132": {
    "inputs": {
      "value": 6
    },
    "class_type": "PrimitiveFloat",
    "_meta": {
      "title": "Float (Duration)"
    }
  },
  "136": {
    "inputs": {
      "prompt": [
        "138",
        0
      ],
      "width": [
        "115",
        0
      ],
      "height": [
        "115",
        1
      ],
      "length": [
        "131",
        1
      ],
      "task_type": "auto",
      "audio_mode": "native",
      "audio_denoise_strength": 1,
      "add_source_as_reference": False,
      "prompt_primary_audio_ordinal": 0,
      "strict_prompt_tags": True,
      "ref_image_size": "match",
      "reference_video_policy": "official_2_to_15s",
      "allow_above_reference_area": True,
      "clip": [
        "128",
        0
      ],
      "video_vae": [
        "119",
        0
      ],
      "audio_vae": [
        "120",
        0
      ],
      "ref_images.ref_image_0": [
        "139",
        0
      ],
      "ref_images.ref_image_1": [
        "256",
        0
      ],
      "ref_images.ref_image_2": [
        "257",
        0
      ],
      "ref_audios.ref_audio_0": [
        "276",
        2
      ]
    },
    "class_type": "MiniMaxH3AudioConditioningT8",
    "_meta": {
      "title": "T8 条件节点｜通用模式"
    }
  },
  "138": {
    "inputs": {
      "value": "subject_definitions:\\n<Subject 1> is Lin Che from <Picture 1>, a 29-year-old Chinese woman with a chin-length black bob, a small mole at the outer end of her left eyebrow, a dark red buttoned knitted cardigan over a white crew-neck top and black trousers. Preserve her facial identity, natural skin and wardrobe; the three standing views do not dictate her seated performance.\\n<Subject 2> is Chen Li from <Picture 2>, a 48-year-old Chinese man with a square face, short black hair graying at the temples, a slight gap in his right eyebrow, a medium-gray knitted cardigan over a pale blue shirt and dark gray trousers. Preserve his face, age, hair and clothing, not the reference pose.\\n<Subject 3> is the same empty meeting room from <Picture 3>: a matte light-gray rectangular table with its long axis east-west, one chair at each east and west short end, a closed high frosted window in the north wall, a low dark-green six-cubby cabinet against the west wall and a closed brown door in the south wall. Preserve the world-space layout and matte surfaces. Omit the four-view borders, reference viewpoints and incidental objects; the room contains only the two directed people and the one directed recorder.\\n\\nsummary:\\n[reference generation] A 6-second continuous live-action medium shot in <Subject 3>. Lin Che establishes that the recorder is already running and challenges Chen Li to speak on record. The three pictures supply identity and room design, with newly directed framing rather than exact endpoints.\\n\\nretention_analysis:\\n<Subject 1> (appears in [Shot 1]): fully_preserved - Keep Lin Che's identity, bob, dark red cardigan and white inner top while directing the specified seated performance.\\n<Subject 2> (appears in [Shot 1]): fully_preserved - Keep Chen Li's identity, gray temples, gray cardigan and pale blue shirt; the directed seated pose replaces the standing reference.\\n<Subject 3> (appears in [Shot 1]): partially_preserved - Keep the fixed room topology, north-window light, west cabinet and table material; omit multi-view panels and reference framing. The initial camera composition is newly directed.\\n\\ndetailed_description:\\nThe target video is a restrained contemporary Chinese live-action suspense drama, with natural skin texture, readable faces and softly lit matte surfaces.\\n[Shot 1] The camera occupies the open southeast aisle at approximately (1.5,-1.5,1.3) meters relative to the table center and faces northwest toward <Subject 1>. She is seated at the west end on screen-left, torso and head turned east toward <Subject 2>, with her gaze going screen-right. Her chin-length bob, natural eyebrow mark and dark red cardigan remain visible. His gray-clad shoulder and pale blue collar occupy only the extreme right foreground; his body remains at the east seat, and his shoulder does not obscure her face, hands or the recorder. The background shows the west green cabinet and only a geometrically plausible part of the north wall and window. The south door stays behind the camera and out of frame.\\nBoth remain seated on the same two chairs, feet on the floor, with neither changing seats or turning away. <Subject 1>'s two empty hands rest separately on the west table edge; <Subject 2>'s left hand rests on the east edge. There is exactly one small black rectangular audio recorder, about 10 by 3 by 1 centimeters, lying flat on the matte tabletop, long axis east-west and its single red indicator steadily lit. It has no readable display. Its center is 0.35 meters east and 0.12 meters south of the table center. His right fingertips rest on the tabletop three centimeters east of the recorder, separated from its casing. The recorder and both hands remain still until any explicitly directed action.\\nHold the initial pose for about one second. <Subject 1> (S1), using a clear low young-adult female Mandarin voice, measured and direct, says <d>[Chinese] 录音开着。你还要我关掉？</d> The statement about recording is a condition of this conversation, not a command to press a button. Finish speaking by about 4.5 seconds, close the mouth and hold eye contact for the remaining beat. Only speech-related lips, small facial tension and natural breathing change. The listener keeps a closed mouth and still hands. No control is pressed, and the indicator remains steadily red.\\nThe sole key is diffused cool-neutral daylight from the fixed high north window, above seated eye level. It softly illuminates the north-facing cheek, the upper knuckles and the recorder's top plane. Weak, slightly warm bounce from the south wall preserves detail on the shadow side without creating another hard shadow. Hair casts a gentle edge at the jaw, and sleeves retain soft folds. Small contact shadows attach hands and the recorder to the tabletop and extend toward the south in world space; the stationary recorder retains a stationary contact shadow. Keep source positions, exposure and white balance steady. Matte surfaces produce subdued highlights rather than flashes. Changing the viewpoint must not relocate the light to the camera side.\\nUse a 40 mm-equivalent lens at seated eye height, in a medium composition with enough depth of field for the featured face, hands and recorder to remain legible. Focus stays on the featured person's eyes without a focus pull. The camera remains fixed throughout; position, orientation, focal length and framing stay unchanged. The foreground shoulder remains a narrow edge element, not a moving wipe or obstruction. Keep the same single shot from beginning to end.\\nThe output is one full-frame scene, with no reference panels, additional people, automatic captions or decorative overlays. Preserve the settled end pose for the adjacent reverse-angle cut.\\n\\noverall_soundscape:\\nLow steady ventilation and distant, muffled room ambience, with subtle breaths and fabric noise. The stationary recorder produces no playback, beeps or repeated scrape. Keep the room tone unobtrusive beneath the voice.\\n\\nnon_diegetic_music:\\nN/A"
    },
    "class_type": "PrimitiveStringMultiline",
    "_meta": {
      "title": "Input Text (Prompt)"
    }
  },
  "139": {
    "inputs": {
      "image": "2636c786c4c0e6c33db28ba14bbe1c381ed4f7cbd8ae925b745e370640e55fea.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "141": {
    "inputs": {
      "max_resolution": 1024,
      "jpeg_quality": 80,
      "suppress_default_preview": True,
      "preview_frames": [
        "131",
        1
      ],
      "preview_fps": 12,
      "tiny_vae": "taeh3.safetensors",
      "model": [
        "178",
        0
      ]
    },
    "class_type": "ModelPreviewOverrideKJ",
    "_meta": {
      "title": "Model Preview Override KJ"
    }
  },
  "147": {
    "inputs": {
      "lora_name": "minimax_h3_ref2v_turbo_8step_v1.0_768p_comfyui_bf16.safetensors",
      "strength_model": 1.0000000000000002,
      "model": [
        "127",
        0
      ]
    },
    "class_type": "LoraLoaderModelOnly",
    "_meta": {
      "title": "Load LoRA"
    }
  },
  "149": {
    "inputs": {
      "shift_video": 12,
      "shift_audio": 3,
      "model": [
        "147",
        0
      ]
    },
    "class_type": "MiniMaxH3SigmaShift",
    "_meta": {
      "title": "ModelSamplingMiniMaxH3"
    }
  },
  "178": {
    "inputs": {
      "attention": "comfy kitchen attention",
      "model": [
        "149",
        0
      ]
    },
    "class_type": "ModelAttentionBackend",
    "_meta": {
      "title": "ModelAttentionBackend"
    }
  },
  "208": {
    "inputs": {
      "step": 6,
      "sigmas": [
        "254",
        0
      ]
    },
    "class_type": "SplitSigmas",
    "_meta": {
      "title": "SplitSigmas"
    }
  },
  "209": {
    "inputs": {
      "noise": [
        "129",
        0
      ],
      "guider": [
        "126",
        0
      ],
      "sampler": [
        "123",
        0
      ],
      "sigmas": [
        "208",
        1
      ],
      "latent_image": [
        "212",
        0
      ]
    },
    "class_type": "SamplerCustomAdvanced",
    "_meta": {
      "title": "SamplerCustomAdvanced"
    }
  },
  "211": {
    "inputs": {
      "av_latent": [
        "125",
        1
      ]
    },
    "class_type": "LTXVSeparateAVLatent",
    "_meta": {
      "title": "Separate AV Latent"
    }
  },
  "212": {
    "inputs": {
      "video_latent": [
        "263",
        0
      ],
      "audio_latent": [
        "211",
        1
      ]
    },
    "class_type": "LTXVConcatAVLatent",
    "_meta": {
      "title": "Concat AV Latent"
    }
  },
  "218": {
    "inputs": {
      "samples": [
        "209",
        0
      ],
      "vae": [
        "120",
        0
      ]
    },
    "class_type": "VAEDecodeAudio",
    "_meta": {
      "title": "VAE Decode Audio"
    }
  },
  "219": {
    "inputs": {
      "samples": [
        "209",
        0
      ],
      "vae": [
        "119",
        0
      ]
    },
    "class_type": "VAEDecode",
    "_meta": {
      "title": "VAE Decode"
    }
  },
  "254": {
    "inputs": {
      "extra_steps": 1,
      "start_at_sigma": 0.7,
      "end_at_sigma": 0,
      "spacing": "cosine",
      "sigmas": [
        "124",
        0
      ]
    },
    "class_type": "H3SigmaRefiner",
    "_meta": {
      "title": "H3 Sigma Refiner"
    }
  },
  "256": {
    "inputs": {
      "image": "07d2e1d22673808899bba100354351b0d4b5b723a10358c7a9ffe92ec0c98ddc.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "257": {
    "inputs": {
      "image": "56a596334282d0057a0847e7a1f2714e8aa27725718b5a162e3ac33c02e42b17.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "258": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "259": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "260": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "263": {
    "inputs": {
      "model_name": "minimax_h3_latent_upscaler_3d_fp16.safetensors",
      "mode": "scale by multiplier",
      "mode.scale": 2,
      "align": 32,
      "device": "cuda",
      "precision": "fp16",
      "enable_chunking": True,
      "latent": [
        "211",
        0
      ]
    },
    "class_type": "MinimaxH3LatentUpscaler3D",
    "_meta": {
      "title": "Minimax H3 Latent Upscaler (3D)"
    }
  },
  "271": {
    "inputs": {
      "frame_rate": 24,
      "loop_count": 0,
      "filename_prefix": "第二次采样",
      "format": "video/h264-mp4",
      "pix_fmt": "yuv420p",
      "crf": 19,
      "save_metadata": True,
      "trim_to_audio": False,
      "pingpong": False,
      "save_output": True,
      "no_preview": False,
      "images": [
        "219",
        0
      ],
      "audio": [
        "218",
        0
      ]
    },
    "class_type": "VHS_VideoCombine",
    "_meta": {
      "title": "Video Combine 🎥🅥🅗🅢"
    }
  },
  "272": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "273": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "274": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "276": {
    "inputs": {
      "video": "1657d341db3688d8d05445f775e8692a0041b27116db8b746fbc5c96a829deb1.mp4",
      "force_rate": 24,
      "force_size": "Disabled",
      "custom_width": 0,
      "custom_height": 0,
      "frame_load_cap": 0,
      "skip_first_frames": 0,
      "select_every_nth": 1,
      "format": "AnimateDiff"
    },
    "class_type": "VHS_LoadVideo",
    "_meta": {
      "title": "Load Video (Upload) 🎥🅥🅗🅢"
    }
  }
}

# minimax_h3 2张图片加上1个参考视频的背景音频
minimax_h3_2_image_1_video_json = {
  "115": {
    "inputs": {
      "aspect_ratio": "16:9 (Widescreen)",
      "megapixels": 0.5,
      "multiple": 32
    },
    "class_type": "ResolutionSelector",
    "_meta": {
      "title": "PASS1 / 16:9 / 0.5MP"
    }
  },
  "119": {
    "inputs": {
      "vae_name": "minimax_h3_video_vae_fp16.safetensors"
    },
    "class_type": "VAELoader",
    "_meta": {
      "title": "Load VAE"
    }
  },
  "120": {
    "inputs": {
      "vae_name": "minimax_h3_audio_vae_fp32.safetensors"
    },
    "class_type": "VAELoader",
    "_meta": {
      "title": "Load VAE"
    }
  },
  "123": {
    "inputs": {
      "sampler_name": "euler"
    },
    "class_type": "KSamplerSelect",
    "_meta": {
      "title": "KSamplerSelect"
    }
  },
  "124": {
    "inputs": {
      "scheduler": "simple",
      "steps": 10,
      "denoise": 1,
      "model": [
        "141",
        0
      ]
    },
    "class_type": "BasicScheduler",
    "_meta": {
      "title": "BasicScheduler"
    }
  },
  "125": {
    "inputs": {
      "noise": [
        "129",
        0
      ],
      "guider": [
        "126",
        0
      ],
      "sampler": [
        "123",
        0
      ],
      "sigmas": [
        "208",
        0
      ],
      "latent_image": [
        "136",
        1
      ]
    },
    "class_type": "SamplerCustomAdvanced",
    "_meta": {
      "title": "SamplerCustomAdvanced"
    }
  },
  "126": {
    "inputs": {
      "model": [
        "141",
        0
      ],
      "conditioning": [
        "136",
        0
      ]
    },
    "class_type": "BasicGuider",
    "_meta": {
      "title": "Basic Guider"
    }
  },
  "127": {
    "inputs": {
      "unet_name": "minimax_h3_hybrid_fl2va_ref2va_b25-49-int8.safetensors",
      "weight_dtype": "default"
    },
    "class_type": "UNETLoader",
    "_meta": {
      "title": "Load Diffusion Model"
    }
  },
  "128": {
    "inputs": {
      "clip_name": "qwen3vl_32b_minimax_h3_int8_convrot.safetensors",
      "type": "minimax",
      "device": "default"
    },
    "class_type": "CLIPLoader",
    "_meta": {
      "title": "Load CLIP"
    }
  },
  "129": {
    "inputs": {
      "noise_seed": 999
    },
    "class_type": "RandomNoise",
    "_meta": {
      "title": "RandomNoise"
    }
  },
  "131": {
    "inputs": {
      "expression": "max(5, round(a * 24)) + (5 - (max(5, round(a * 24)) % 17)) % 17",
      "values.a": [
        "132",
        0
      ]
    },
    "class_type": "ComfyMathExpression",
    "_meta": {
      "title": "Math Expression"
    }
  },
  "132": {
    "inputs": {
      "value": 6
    },
    "class_type": "PrimitiveFloat",
    "_meta": {
      "title": "Float (Duration)"
    }
  },
  "136": {
    "inputs": {
      "prompt": [
        "138",
        0
      ],
      "width": [
        "115",
        0
      ],
      "height": [
        "115",
        1
      ],
      "length": [
        "131",
        1
      ],
      "task_type": "auto",
      "audio_mode": "native",
      "audio_denoise_strength": 1,
      "add_source_as_reference": False,
      "prompt_primary_audio_ordinal": 0,
      "strict_prompt_tags": True,
      "ref_image_size": "match",
      "reference_video_policy": "official_2_to_15s",
      "allow_above_reference_area": True,
      "clip": [
        "128",
        0
      ],
      "video_vae": [
        "119",
        0
      ],
      "audio_vae": [
        "120",
        0
      ],
      "ref_images.ref_image_0": [
        "139",
        0
      ],
      "ref_images.ref_image_1": [
        "256",
        0
      ],
      "ref_audios.ref_audio_0": [
        "276",
        2
      ]
    },
    "class_type": "MiniMaxH3AudioConditioningT8",
    "_meta": {
      "title": "T8 条件节点｜通用模式"
    }
  },
  "138": {
    "inputs": {
      "value": "subject_definitions:\\n<Subject 1> is Lin Che from <Picture 1>, a 29-year-old Chinese woman with a chin-length black bob, a small mole at the outer end of her left eyebrow, a dark red buttoned knitted cardigan over a white crew-neck top and black trousers. Preserve her facial identity, natural skin and wardrobe; the three standing views do not dictate her seated performance.\\n<Subject 2> is Chen Li from <Picture 2>, a 48-year-old Chinese man with a square face, short black hair graying at the temples, a slight gap in his right eyebrow, a medium-gray knitted cardigan over a pale blue shirt and dark gray trousers. Preserve his face, age, hair and clothing, not the reference pose.\\n<Subject 3> is the same empty meeting room from <Picture 3>: a matte light-gray rectangular table with its long axis east-west, one chair at each east and west short end, a closed high frosted window in the north wall, a low dark-green six-cubby cabinet against the west wall and a closed brown door in the south wall. Preserve the world-space layout and matte surfaces. Omit the four-view borders, reference viewpoints and incidental objects; the room contains only the two directed people and the one directed recorder.\\n\\nsummary:\\n[reference generation] A 6-second continuous live-action medium shot in <Subject 3>. Lin Che establishes that the recorder is already running and challenges Chen Li to speak on record. The three pictures supply identity and room design, with newly directed framing rather than exact endpoints.\\n\\nretention_analysis:\\n<Subject 1> (appears in [Shot 1]): fully_preserved - Keep Lin Che's identity, bob, dark red cardigan and white inner top while directing the specified seated performance.\\n<Subject 2> (appears in [Shot 1]): fully_preserved - Keep Chen Li's identity, gray temples, gray cardigan and pale blue shirt; the directed seated pose replaces the standing reference.\\n<Subject 3> (appears in [Shot 1]): partially_preserved - Keep the fixed room topology, north-window light, west cabinet and table material; omit multi-view panels and reference framing. The initial camera composition is newly directed.\\n\\ndetailed_description:\\nThe target video is a restrained contemporary Chinese live-action suspense drama, with natural skin texture, readable faces and softly lit matte surfaces.\\n[Shot 1] The camera occupies the open southeast aisle at approximately (1.5,-1.5,1.3) meters relative to the table center and faces northwest toward <Subject 1>. She is seated at the west end on screen-left, torso and head turned east toward <Subject 2>, with her gaze going screen-right. Her chin-length bob, natural eyebrow mark and dark red cardigan remain visible. His gray-clad shoulder and pale blue collar occupy only the extreme right foreground; his body remains at the east seat, and his shoulder does not obscure her face, hands or the recorder. The background shows the west green cabinet and only a geometrically plausible part of the north wall and window. The south door stays behind the camera and out of frame.\\nBoth remain seated on the same two chairs, feet on the floor, with neither changing seats or turning away. <Subject 1>'s two empty hands rest separately on the west table edge; <Subject 2>'s left hand rests on the east edge. There is exactly one small black rectangular audio recorder, about 10 by 3 by 1 centimeters, lying flat on the matte tabletop, long axis east-west and its single red indicator steadily lit. It has no readable display. Its center is 0.35 meters east and 0.12 meters south of the table center. His right fingertips rest on the tabletop three centimeters east of the recorder, separated from its casing. The recorder and both hands remain still until any explicitly directed action.\\nHold the initial pose for about one second. <Subject 1> (S1), using a clear low young-adult female Mandarin voice, measured and direct, says <d>[Chinese] 录音开着。你还要我关掉？</d> The statement about recording is a condition of this conversation, not a command to press a button. Finish speaking by about 4.5 seconds, close the mouth and hold eye contact for the remaining beat. Only speech-related lips, small facial tension and natural breathing change. The listener keeps a closed mouth and still hands. No control is pressed, and the indicator remains steadily red.\\nThe sole key is diffused cool-neutral daylight from the fixed high north window, above seated eye level. It softly illuminates the north-facing cheek, the upper knuckles and the recorder's top plane. Weak, slightly warm bounce from the south wall preserves detail on the shadow side without creating another hard shadow. Hair casts a gentle edge at the jaw, and sleeves retain soft folds. Small contact shadows attach hands and the recorder to the tabletop and extend toward the south in world space; the stationary recorder retains a stationary contact shadow. Keep source positions, exposure and white balance steady. Matte surfaces produce subdued highlights rather than flashes. Changing the viewpoint must not relocate the light to the camera side.\\nUse a 40 mm-equivalent lens at seated eye height, in a medium composition with enough depth of field for the featured face, hands and recorder to remain legible. Focus stays on the featured person's eyes without a focus pull. The camera remains fixed throughout; position, orientation, focal length and framing stay unchanged. The foreground shoulder remains a narrow edge element, not a moving wipe or obstruction. Keep the same single shot from beginning to end.\\nThe output is one full-frame scene, with no reference panels, additional people, automatic captions or decorative overlays. Preserve the settled end pose for the adjacent reverse-angle cut.\\n\\noverall_soundscape:\\nLow steady ventilation and distant, muffled room ambience, with subtle breaths and fabric noise. The stationary recorder produces no playback, beeps or repeated scrape. Keep the room tone unobtrusive beneath the voice.\\n\\nnon_diegetic_music:\\nN/A"
    },
    "class_type": "PrimitiveStringMultiline",
    "_meta": {
      "title": "Input Text (Prompt)"
    }
  },
  "139": {
    "inputs": {
      "image": "2636c786c4c0e6c33db28ba14bbe1c381ed4f7cbd8ae925b745e370640e55fea.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "141": {
    "inputs": {
      "max_resolution": 1024,
      "jpeg_quality": 80,
      "suppress_default_preview": True,
      "preview_frames": [
        "131",
        1
      ],
      "preview_fps": 12,
      "tiny_vae": "taeh3.safetensors",
      "model": [
        "178",
        0
      ]
    },
    "class_type": "ModelPreviewOverrideKJ",
    "_meta": {
      "title": "Model Preview Override KJ"
    }
  },
  "147": {
    "inputs": {
      "lora_name": "minimax_h3_ref2v_turbo_8step_v1.0_768p_comfyui_bf16.safetensors",
      "strength_model": 1.0000000000000002,
      "model": [
        "127",
        0
      ]
    },
    "class_type": "LoraLoaderModelOnly",
    "_meta": {
      "title": "Load LoRA"
    }
  },
  "149": {
    "inputs": {
      "shift_video": 12,
      "shift_audio": 3,
      "model": [
        "147",
        0
      ]
    },
    "class_type": "MiniMaxH3SigmaShift",
    "_meta": {
      "title": "ModelSamplingMiniMaxH3"
    }
  },
  "178": {
    "inputs": {
      "attention": "comfy kitchen attention",
      "model": [
        "149",
        0
      ]
    },
    "class_type": "ModelAttentionBackend",
    "_meta": {
      "title": "ModelAttentionBackend"
    }
  },
  "208": {
    "inputs": {
      "step": 6,
      "sigmas": [
        "254",
        0
      ]
    },
    "class_type": "SplitSigmas",
    "_meta": {
      "title": "SplitSigmas"
    }
  },
  "209": {
    "inputs": {
      "noise": [
        "129",
        0
      ],
      "guider": [
        "126",
        0
      ],
      "sampler": [
        "123",
        0
      ],
      "sigmas": [
        "208",
        1
      ],
      "latent_image": [
        "212",
        0
      ]
    },
    "class_type": "SamplerCustomAdvanced",
    "_meta": {
      "title": "SamplerCustomAdvanced"
    }
  },
  "211": {
    "inputs": {
      "av_latent": [
        "125",
        1
      ]
    },
    "class_type": "LTXVSeparateAVLatent",
    "_meta": {
      "title": "Separate AV Latent"
    }
  },
  "212": {
    "inputs": {
      "video_latent": [
        "263",
        0
      ],
      "audio_latent": [
        "211",
        1
      ]
    },
    "class_type": "LTXVConcatAVLatent",
    "_meta": {
      "title": "Concat AV Latent"
    }
  },
  "218": {
    "inputs": {
      "samples": [
        "209",
        0
      ],
      "vae": [
        "120",
        0
      ]
    },
    "class_type": "VAEDecodeAudio",
    "_meta": {
      "title": "VAE Decode Audio"
    }
  },
  "219": {
    "inputs": {
      "samples": [
        "209",
        0
      ],
      "vae": [
        "119",
        0
      ]
    },
    "class_type": "VAEDecode",
    "_meta": {
      "title": "VAE Decode"
    }
  },
  "254": {
    "inputs": {
      "extra_steps": 1,
      "start_at_sigma": 0.7,
      "end_at_sigma": 0,
      "spacing": "cosine",
      "sigmas": [
        "124",
        0
      ]
    },
    "class_type": "H3SigmaRefiner",
    "_meta": {
      "title": "H3 Sigma Refiner"
    }
  },
  "256": {
    "inputs": {
      "image": "07d2e1d22673808899bba100354351b0d4b5b723a10358c7a9ffe92ec0c98ddc.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "257": {
    "inputs": {
      "image": "56a596334282d0057a0847e7a1f2714e8aa27725718b5a162e3ac33c02e42b17.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "258": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "259": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "260": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "263": {
    "inputs": {
      "model_name": "minimax_h3_latent_upscaler_3d_fp16.safetensors",
      "mode": "scale by multiplier",
      "mode.scale": 2,
      "align": 32,
      "device": "cuda",
      "precision": "fp16",
      "enable_chunking": True,
      "latent": [
        "211",
        0
      ]
    },
    "class_type": "MinimaxH3LatentUpscaler3D",
    "_meta": {
      "title": "Minimax H3 Latent Upscaler (3D)"
    }
  },
  "271": {
    "inputs": {
      "frame_rate": 24,
      "loop_count": 0,
      "filename_prefix": "第二次采样",
      "format": "video/h264-mp4",
      "pix_fmt": "yuv420p",
      "crf": 19,
      "save_metadata": True,
      "trim_to_audio": False,
      "pingpong": False,
      "save_output": True,
      "no_preview": False,
      "images": [
        "219",
        0
      ],
      "audio": [
        "218",
        0
      ]
    },
    "class_type": "VHS_VideoCombine",
    "_meta": {
      "title": "Video Combine 🎥🅥🅗🅢"
    }
  },
  "272": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "273": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "274": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "276": {
    "inputs": {
      "video": "1657d341db3688d8d05445f775e8692a0041b27116db8b746fbc5c96a829deb1.mp4",
      "force_rate": 24,
      "force_size": "Disabled",
      "custom_width": 0,
      "custom_height": 0,
      "frame_load_cap": 0,
      "skip_first_frames": 0,
      "select_every_nth": 1,
      "format": "AnimateDiff"
    },
    "class_type": "VHS_LoadVideo",
    "_meta": {
      "title": "Load Video (Upload) 🎥🅥🅗🅢"
    }
  }
}

# minimax_h3 1张图片加上1个参考视频的背景音频
minimax_h3_1_image_1_video_json = {
  "115": {
    "inputs": {
      "aspect_ratio": "16:9 (Widescreen)",
      "megapixels": 0.5,
      "multiple": 32
    },
    "class_type": "ResolutionSelector",
    "_meta": {
      "title": "PASS1 / 16:9 / 0.5MP"
    }
  },
  "119": {
    "inputs": {
      "vae_name": "minimax_h3_video_vae_fp16.safetensors"
    },
    "class_type": "VAELoader",
    "_meta": {
      "title": "Load VAE"
    }
  },
  "120": {
    "inputs": {
      "vae_name": "minimax_h3_audio_vae_fp32.safetensors"
    },
    "class_type": "VAELoader",
    "_meta": {
      "title": "Load VAE"
    }
  },
  "123": {
    "inputs": {
      "sampler_name": "euler"
    },
    "class_type": "KSamplerSelect",
    "_meta": {
      "title": "KSamplerSelect"
    }
  },
  "124": {
    "inputs": {
      "scheduler": "simple",
      "steps": 10,
      "denoise": 1,
      "model": [
        "141",
        0
      ]
    },
    "class_type": "BasicScheduler",
    "_meta": {
      "title": "BasicScheduler"
    }
  },
  "125": {
    "inputs": {
      "noise": [
        "129",
        0
      ],
      "guider": [
        "126",
        0
      ],
      "sampler": [
        "123",
        0
      ],
      "sigmas": [
        "208",
        0
      ],
      "latent_image": [
        "136",
        1
      ]
    },
    "class_type": "SamplerCustomAdvanced",
    "_meta": {
      "title": "SamplerCustomAdvanced"
    }
  },
  "126": {
    "inputs": {
      "model": [
        "141",
        0
      ],
      "conditioning": [
        "136",
        0
      ]
    },
    "class_type": "BasicGuider",
    "_meta": {
      "title": "Basic Guider"
    }
  },
  "127": {
    "inputs": {
      "unet_name": "minimax_h3_hybrid_fl2va_ref2va_b25-49-int8.safetensors",
      "weight_dtype": "default"
    },
    "class_type": "UNETLoader",
    "_meta": {
      "title": "Load Diffusion Model"
    }
  },
  "128": {
    "inputs": {
      "clip_name": "qwen3vl_32b_minimax_h3_int8_convrot.safetensors",
      "type": "minimax",
      "device": "default"
    },
    "class_type": "CLIPLoader",
    "_meta": {
      "title": "Load CLIP"
    }
  },
  "129": {
    "inputs": {
      "noise_seed": 999
    },
    "class_type": "RandomNoise",
    "_meta": {
      "title": "RandomNoise"
    }
  },
  "131": {
    "inputs": {
      "expression": "max(5, round(a * 24)) + (5 - (max(5, round(a * 24)) % 17)) % 17",
      "values.a": [
        "132",
        0
      ]
    },
    "class_type": "ComfyMathExpression",
    "_meta": {
      "title": "Math Expression"
    }
  },
  "132": {
    "inputs": {
      "value": 6
    },
    "class_type": "PrimitiveFloat",
    "_meta": {
      "title": "Float (Duration)"
    }
  },
  "136": {
    "inputs": {
      "prompt": [
        "138",
        0
      ],
      "width": [
        "115",
        0
      ],
      "height": [
        "115",
        1
      ],
      "length": [
        "131",
        1
      ],
      "task_type": "auto",
      "audio_mode": "native",
      "audio_denoise_strength": 1,
      "add_source_as_reference": False,
      "prompt_primary_audio_ordinal": 0,
      "strict_prompt_tags": True,
      "ref_image_size": "match",
      "reference_video_policy": "official_2_to_15s",
      "allow_above_reference_area": True,
      "clip": [
        "128",
        0
      ],
      "video_vae": [
        "119",
        0
      ],
      "audio_vae": [
        "120",
        0
      ],
      "ref_images.ref_image_0": [
        "139",
        0
      ],
      "ref_audios.ref_audio_0": [
        "276",
        2
      ]
    },
    "class_type": "MiniMaxH3AudioConditioningT8",
    "_meta": {
      "title": "T8 条件节点｜通用模式"
    }
  },
  "138": {
    "inputs": {
      "value": "subject_definitions:\\n<Subject 1> is Lin Che from <Picture 1>, a 29-year-old Chinese woman with a chin-length black bob, a small mole at the outer end of her left eyebrow, a dark red buttoned knitted cardigan over a white crew-neck top and black trousers. Preserve her facial identity, natural skin and wardrobe; the three standing views do not dictate her seated performance.\\n<Subject 2> is Chen Li from <Picture 2>, a 48-year-old Chinese man with a square face, short black hair graying at the temples, a slight gap in his right eyebrow, a medium-gray knitted cardigan over a pale blue shirt and dark gray trousers. Preserve his face, age, hair and clothing, not the reference pose.\\n<Subject 3> is the same empty meeting room from <Picture 3>: a matte light-gray rectangular table with its long axis east-west, one chair at each east and west short end, a closed high frosted window in the north wall, a low dark-green six-cubby cabinet against the west wall and a closed brown door in the south wall. Preserve the world-space layout and matte surfaces. Omit the four-view borders, reference viewpoints and incidental objects; the room contains only the two directed people and the one directed recorder.\\n\\nsummary:\\n[reference generation] A 6-second continuous live-action medium shot in <Subject 3>. Lin Che establishes that the recorder is already running and challenges Chen Li to speak on record. The three pictures supply identity and room design, with newly directed framing rather than exact endpoints.\\n\\nretention_analysis:\\n<Subject 1> (appears in [Shot 1]): fully_preserved - Keep Lin Che's identity, bob, dark red cardigan and white inner top while directing the specified seated performance.\\n<Subject 2> (appears in [Shot 1]): fully_preserved - Keep Chen Li's identity, gray temples, gray cardigan and pale blue shirt; the directed seated pose replaces the standing reference.\\n<Subject 3> (appears in [Shot 1]): partially_preserved - Keep the fixed room topology, north-window light, west cabinet and table material; omit multi-view panels and reference framing. The initial camera composition is newly directed.\\n\\ndetailed_description:\\nThe target video is a restrained contemporary Chinese live-action suspense drama, with natural skin texture, readable faces and softly lit matte surfaces.\\n[Shot 1] The camera occupies the open southeast aisle at approximately (1.5,-1.5,1.3) meters relative to the table center and faces northwest toward <Subject 1>. She is seated at the west end on screen-left, torso and head turned east toward <Subject 2>, with her gaze going screen-right. Her chin-length bob, natural eyebrow mark and dark red cardigan remain visible. His gray-clad shoulder and pale blue collar occupy only the extreme right foreground; his body remains at the east seat, and his shoulder does not obscure her face, hands or the recorder. The background shows the west green cabinet and only a geometrically plausible part of the north wall and window. The south door stays behind the camera and out of frame.\\nBoth remain seated on the same two chairs, feet on the floor, with neither changing seats or turning away. <Subject 1>'s two empty hands rest separately on the west table edge; <Subject 2>'s left hand rests on the east edge. There is exactly one small black rectangular audio recorder, about 10 by 3 by 1 centimeters, lying flat on the matte tabletop, long axis east-west and its single red indicator steadily lit. It has no readable display. Its center is 0.35 meters east and 0.12 meters south of the table center. His right fingertips rest on the tabletop three centimeters east of the recorder, separated from its casing. The recorder and both hands remain still until any explicitly directed action.\\nHold the initial pose for about one second. <Subject 1> (S1), using a clear low young-adult female Mandarin voice, measured and direct, says <d>[Chinese] 录音开着。你还要我关掉？</d> The statement about recording is a condition of this conversation, not a command to press a button. Finish speaking by about 4.5 seconds, close the mouth and hold eye contact for the remaining beat. Only speech-related lips, small facial tension and natural breathing change. The listener keeps a closed mouth and still hands. No control is pressed, and the indicator remains steadily red.\\nThe sole key is diffused cool-neutral daylight from the fixed high north window, above seated eye level. It softly illuminates the north-facing cheek, the upper knuckles and the recorder's top plane. Weak, slightly warm bounce from the south wall preserves detail on the shadow side without creating another hard shadow. Hair casts a gentle edge at the jaw, and sleeves retain soft folds. Small contact shadows attach hands and the recorder to the tabletop and extend toward the south in world space; the stationary recorder retains a stationary contact shadow. Keep source positions, exposure and white balance steady. Matte surfaces produce subdued highlights rather than flashes. Changing the viewpoint must not relocate the light to the camera side.\\nUse a 40 mm-equivalent lens at seated eye height, in a medium composition with enough depth of field for the featured face, hands and recorder to remain legible. Focus stays on the featured person's eyes without a focus pull. The camera remains fixed throughout; position, orientation, focal length and framing stay unchanged. The foreground shoulder remains a narrow edge element, not a moving wipe or obstruction. Keep the same single shot from beginning to end.\\nThe output is one full-frame scene, with no reference panels, additional people, automatic captions or decorative overlays. Preserve the settled end pose for the adjacent reverse-angle cut.\\n\\noverall_soundscape:\\nLow steady ventilation and distant, muffled room ambience, with subtle breaths and fabric noise. The stationary recorder produces no playback, beeps or repeated scrape. Keep the room tone unobtrusive beneath the voice.\\n\\nnon_diegetic_music:\\nN/A"
    },
    "class_type": "PrimitiveStringMultiline",
    "_meta": {
      "title": "Input Text (Prompt)"
    }
  },
  "139": {
    "inputs": {
      "image": "2636c786c4c0e6c33db28ba14bbe1c381ed4f7cbd8ae925b745e370640e55fea.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "141": {
    "inputs": {
      "max_resolution": 1024,
      "jpeg_quality": 80,
      "suppress_default_preview": True,
      "preview_frames": [
        "131",
        1
      ],
      "preview_fps": 12,
      "tiny_vae": "taeh3.safetensors",
      "model": [
        "178",
        0
      ]
    },
    "class_type": "ModelPreviewOverrideKJ",
    "_meta": {
      "title": "Model Preview Override KJ"
    }
  },
  "147": {
    "inputs": {
      "lora_name": "minimax_h3_ref2v_turbo_8step_v1.0_768p_comfyui_bf16.safetensors",
      "strength_model": 1.0000000000000002,
      "model": [
        "127",
        0
      ]
    },
    "class_type": "LoraLoaderModelOnly",
    "_meta": {
      "title": "Load LoRA"
    }
  },
  "149": {
    "inputs": {
      "shift_video": 12,
      "shift_audio": 3,
      "model": [
        "147",
        0
      ]
    },
    "class_type": "MiniMaxH3SigmaShift",
    "_meta": {
      "title": "ModelSamplingMiniMaxH3"
    }
  },
  "178": {
    "inputs": {
      "attention": "comfy kitchen attention",
      "model": [
        "149",
        0
      ]
    },
    "class_type": "ModelAttentionBackend",
    "_meta": {
      "title": "ModelAttentionBackend"
    }
  },
  "208": {
    "inputs": {
      "step": 6,
      "sigmas": [
        "254",
        0
      ]
    },
    "class_type": "SplitSigmas",
    "_meta": {
      "title": "SplitSigmas"
    }
  },
  "209": {
    "inputs": {
      "noise": [
        "129",
        0
      ],
      "guider": [
        "126",
        0
      ],
      "sampler": [
        "123",
        0
      ],
      "sigmas": [
        "208",
        1
      ],
      "latent_image": [
        "212",
        0
      ]
    },
    "class_type": "SamplerCustomAdvanced",
    "_meta": {
      "title": "SamplerCustomAdvanced"
    }
  },
  "211": {
    "inputs": {
      "av_latent": [
        "125",
        1
      ]
    },
    "class_type": "LTXVSeparateAVLatent",
    "_meta": {
      "title": "Separate AV Latent"
    }
  },
  "212": {
    "inputs": {
      "video_latent": [
        "263",
        0
      ],
      "audio_latent": [
        "211",
        1
      ]
    },
    "class_type": "LTXVConcatAVLatent",
    "_meta": {
      "title": "Concat AV Latent"
    }
  },
  "218": {
    "inputs": {
      "samples": [
        "209",
        0
      ],
      "vae": [
        "120",
        0
      ]
    },
    "class_type": "VAEDecodeAudio",
    "_meta": {
      "title": "VAE Decode Audio"
    }
  },
  "219": {
    "inputs": {
      "samples": [
        "209",
        0
      ],
      "vae": [
        "119",
        0
      ]
    },
    "class_type": "VAEDecode",
    "_meta": {
      "title": "VAE Decode"
    }
  },
  "254": {
    "inputs": {
      "extra_steps": 1,
      "start_at_sigma": 0.7,
      "end_at_sigma": 0,
      "spacing": "cosine",
      "sigmas": [
        "124",
        0
      ]
    },
    "class_type": "H3SigmaRefiner",
    "_meta": {
      "title": "H3 Sigma Refiner"
    }
  },
  "256": {
    "inputs": {
      "image": "07d2e1d22673808899bba100354351b0d4b5b723a10358c7a9ffe92ec0c98ddc.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "257": {
    "inputs": {
      "image": "56a596334282d0057a0847e7a1f2714e8aa27725718b5a162e3ac33c02e42b17.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "258": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "259": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "260": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "263": {
    "inputs": {
      "model_name": "minimax_h3_latent_upscaler_3d_fp16.safetensors",
      "mode": "scale by multiplier",
      "mode.scale": 2,
      "align": 32,
      "device": "cuda",
      "precision": "fp16",
      "enable_chunking": True,
      "latent": [
        "211",
        0
      ]
    },
    "class_type": "MinimaxH3LatentUpscaler3D",
    "_meta": {
      "title": "Minimax H3 Latent Upscaler (3D)"
    }
  },
  "271": {
    "inputs": {
      "frame_rate": 24,
      "loop_count": 0,
      "filename_prefix": "第二次采样",
      "format": "video/h264-mp4",
      "pix_fmt": "yuv420p",
      "crf": 19,
      "save_metadata": True,
      "trim_to_audio": False,
      "pingpong": False,
      "save_output": True,
      "no_preview": False,
      "images": [
        "219",
        0
      ],
      "audio": [
        "218",
        0
      ]
    },
    "class_type": "VHS_VideoCombine",
    "_meta": {
      "title": "Video Combine 🎥🅥🅗🅢"
    }
  },
  "272": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "273": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "274": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "276": {
    "inputs": {
      "video": "1657d341db3688d8d05445f775e8692a0041b27116db8b746fbc5c96a829deb1.mp4",
      "force_rate": 24,
      "force_size": "Disabled",
      "custom_width": 0,
      "custom_height": 0,
      "frame_load_cap": 0,
      "skip_first_frames": 0,
      "select_every_nth": 1,
      "format": "AnimateDiff"
    },
    "class_type": "VHS_LoadVideo",
    "_meta": {
      "title": "Load Video (Upload) 🎥🅥🅗🅢"
    }
  }
}


# minimax_h3 9张图片加上1个参考音频
minimax_h3_9_image_1_audio_json = {
  "115": {
    "inputs": {
      "aspect_ratio": "16:9 (Widescreen)",
      "megapixels": 0.5,
      "multiple": 32
    },
    "class_type": "ResolutionSelector",
    "_meta": {
      "title": "PASS1 / 16:9 / 0.5MP"
    }
  },
  "119": {
    "inputs": {
      "vae_name": "minimax_h3_video_vae_fp16.safetensors"
    },
    "class_type": "VAELoader",
    "_meta": {
      "title": "Load VAE"
    }
  },
  "120": {
    "inputs": {
      "vae_name": "minimax_h3_audio_vae_fp32.safetensors"
    },
    "class_type": "VAELoader",
    "_meta": {
      "title": "Load VAE"
    }
  },
  "123": {
    "inputs": {
      "sampler_name": "euler"
    },
    "class_type": "KSamplerSelect",
    "_meta": {
      "title": "KSamplerSelect"
    }
  },
  "124": {
    "inputs": {
      "scheduler": "simple",
      "steps": 10,
      "denoise": 1,
      "model": [
        "141",
        0
      ]
    },
    "class_type": "BasicScheduler",
    "_meta": {
      "title": "BasicScheduler"
    }
  },
  "125": {
    "inputs": {
      "noise": [
        "129",
        0
      ],
      "guider": [
        "126",
        0
      ],
      "sampler": [
        "123",
        0
      ],
      "sigmas": [
        "208",
        0
      ],
      "latent_image": [
        "136",
        1
      ]
    },
    "class_type": "SamplerCustomAdvanced",
    "_meta": {
      "title": "SamplerCustomAdvanced"
    }
  },
  "126": {
    "inputs": {
      "model": [
        "141",
        0
      ],
      "conditioning": [
        "136",
        0
      ]
    },
    "class_type": "BasicGuider",
    "_meta": {
      "title": "Basic Guider"
    }
  },
  "127": {
    "inputs": {
      "unet_name": "minimax_h3_hybrid_fl2va_ref2va_b25-49-int8.safetensors",
      "weight_dtype": "default"
    },
    "class_type": "UNETLoader",
    "_meta": {
      "title": "Load Diffusion Model"
    }
  },
  "128": {
    "inputs": {
      "clip_name": "qwen3vl_32b_minimax_h3_int8_convrot.safetensors",
      "type": "minimax",
      "device": "default"
    },
    "class_type": "CLIPLoader",
    "_meta": {
      "title": "Load CLIP"
    }
  },
  "129": {
    "inputs": {
      "noise_seed": 999
    },
    "class_type": "RandomNoise",
    "_meta": {
      "title": "RandomNoise"
    }
  },
  "131": {
    "inputs": {
      "expression": "max(5, round(a * 24)) + (5 - (max(5, round(a * 24)) % 17)) % 17",
      "values.a": [
        "132",
        0
      ]
    },
    "class_type": "ComfyMathExpression",
    "_meta": {
      "title": "Math Expression"
    }
  },
  "132": {
    "inputs": {
      "value": 6
    },
    "class_type": "PrimitiveFloat",
    "_meta": {
      "title": "Float (Duration)"
    }
  },
  "136": {
    "inputs": {
      "prompt": [
        "138",
        0
      ],
      "width": [
        "115",
        0
      ],
      "height": [
        "115",
        1
      ],
      "length": [
        "131",
        1
      ],
      "task_type": "auto",
      "audio_mode": "native",
      "audio_denoise_strength": 1,
      "add_source_as_reference": False,
      "prompt_primary_audio_ordinal": 0,
      "strict_prompt_tags": True,
      "ref_image_size": "match",
      "reference_video_policy": "official_2_to_15s",
      "allow_above_reference_area": True,
      "clip": [
        "128",
        0
      ],
      "video_vae": [
        "119",
        0
      ],
      "audio_vae": [
        "120",
        0
      ],
      "ref_images.ref_image_0": [
        "139",
        0
      ],
      "ref_images.ref_image_1": [
        "256",
        0
      ],
      "ref_images.ref_image_2": [
        "257",
        0
      ],
      "ref_images.ref_image_3": [
        "258",
        0
      ],
      "ref_images.ref_image_4": [
        "259",
        0
      ],
      "ref_images.ref_image_5": [
        "260",
        0
      ],
      "ref_images.ref_image_6": [
        "272",
        0
      ],
      "ref_images.ref_image_7": [
        "273",
        0
      ],
      "ref_images.ref_image_8": [
        "274",
        0
      ],
      "ref_audios.ref_audio_0": [
        "275",
        0
      ]
    },
    "class_type": "MiniMaxH3AudioConditioningT8",
    "_meta": {
      "title": "T8 条件节点｜通用模式"
    }
  },
  "138": {
    "inputs": {
      "value": "subject_definitions:\\n<Subject 1> is Lin Che from <Picture 1>, a 29-year-old Chinese woman with a chin-length black bob, a small mole at the outer end of her left eyebrow, a dark red buttoned knitted cardigan over a white crew-neck top and black trousers. Preserve her facial identity, natural skin and wardrobe; the three standing views do not dictate her seated performance.\\n<Subject 2> is Chen Li from <Picture 2>, a 48-year-old Chinese man with a square face, short black hair graying at the temples, a slight gap in his right eyebrow, a medium-gray knitted cardigan over a pale blue shirt and dark gray trousers. Preserve his face, age, hair and clothing, not the reference pose.\\n<Subject 3> is the same empty meeting room from <Picture 3>: a matte light-gray rectangular table with its long axis east-west, one chair at each east and west short end, a closed high frosted window in the north wall, a low dark-green six-cubby cabinet against the west wall and a closed brown door in the south wall. Preserve the world-space layout and matte surfaces. Omit the four-view borders, reference viewpoints and incidental objects; the room contains only the two directed people and the one directed recorder.\\n\\nsummary:\\n[reference generation] A 6-second continuous live-action medium shot in <Subject 3>. Lin Che establishes that the recorder is already running and challenges Chen Li to speak on record. The three pictures supply identity and room design, with newly directed framing rather than exact endpoints.\\n\\nretention_analysis:\\n<Subject 1> (appears in [Shot 1]): fully_preserved - Keep Lin Che's identity, bob, dark red cardigan and white inner top while directing the specified seated performance.\\n<Subject 2> (appears in [Shot 1]): fully_preserved - Keep Chen Li's identity, gray temples, gray cardigan and pale blue shirt; the directed seated pose replaces the standing reference.\\n<Subject 3> (appears in [Shot 1]): partially_preserved - Keep the fixed room topology, north-window light, west cabinet and table material; omit multi-view panels and reference framing. The initial camera composition is newly directed.\\n\\ndetailed_description:\\nThe target video is a restrained contemporary Chinese live-action suspense drama, with natural skin texture, readable faces and softly lit matte surfaces.\\n[Shot 1] The camera occupies the open southeast aisle at approximately (1.5,-1.5,1.3) meters relative to the table center and faces northwest toward <Subject 1>. She is seated at the west end on screen-left, torso and head turned east toward <Subject 2>, with her gaze going screen-right. Her chin-length bob, natural eyebrow mark and dark red cardigan remain visible. His gray-clad shoulder and pale blue collar occupy only the extreme right foreground; his body remains at the east seat, and his shoulder does not obscure her face, hands or the recorder. The background shows the west green cabinet and only a geometrically plausible part of the north wall and window. The south door stays behind the camera and out of frame.\\nBoth remain seated on the same two chairs, feet on the floor, with neither changing seats or turning away. <Subject 1>'s two empty hands rest separately on the west table edge; <Subject 2>'s left hand rests on the east edge. There is exactly one small black rectangular audio recorder, about 10 by 3 by 1 centimeters, lying flat on the matte tabletop, long axis east-west and its single red indicator steadily lit. It has no readable display. Its center is 0.35 meters east and 0.12 meters south of the table center. His right fingertips rest on the tabletop three centimeters east of the recorder, separated from its casing. The recorder and both hands remain still until any explicitly directed action.\\nHold the initial pose for about one second. <Subject 1> (S1), using a clear low young-adult female Mandarin voice, measured and direct, says <d>[Chinese] 录音开着。你还要我关掉？</d> The statement about recording is a condition of this conversation, not a command to press a button. Finish speaking by about 4.5 seconds, close the mouth and hold eye contact for the remaining beat. Only speech-related lips, small facial tension and natural breathing change. The listener keeps a closed mouth and still hands. No control is pressed, and the indicator remains steadily red.\\nThe sole key is diffused cool-neutral daylight from the fixed high north window, above seated eye level. It softly illuminates the north-facing cheek, the upper knuckles and the recorder's top plane. Weak, slightly warm bounce from the south wall preserves detail on the shadow side without creating another hard shadow. Hair casts a gentle edge at the jaw, and sleeves retain soft folds. Small contact shadows attach hands and the recorder to the tabletop and extend toward the south in world space; the stationary recorder retains a stationary contact shadow. Keep source positions, exposure and white balance steady. Matte surfaces produce subdued highlights rather than flashes. Changing the viewpoint must not relocate the light to the camera side.\\nUse a 40 mm-equivalent lens at seated eye height, in a medium composition with enough depth of field for the featured face, hands and recorder to remain legible. Focus stays on the featured person's eyes without a focus pull. The camera remains fixed throughout; position, orientation, focal length and framing stay unchanged. The foreground shoulder remains a narrow edge element, not a moving wipe or obstruction. Keep the same single shot from beginning to end.\\nThe output is one full-frame scene, with no reference panels, additional people, automatic captions or decorative overlays. Preserve the settled end pose for the adjacent reverse-angle cut.\\n\\noverall_soundscape:\\nLow steady ventilation and distant, muffled room ambience, with subtle breaths and fabric noise. The stationary recorder produces no playback, beeps or repeated scrape. Keep the room tone unobtrusive beneath the voice.\\n\\nnon_diegetic_music:\\nN/A"
    },
    "class_type": "PrimitiveStringMultiline",
    "_meta": {
      "title": "Input Text (Prompt)"
    }
  },
  "139": {
    "inputs": {
      "image": "2636c786c4c0e6c33db28ba14bbe1c381ed4f7cbd8ae925b745e370640e55fea.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "141": {
    "inputs": {
      "max_resolution": 1024,
      "jpeg_quality": 80,
      "suppress_default_preview": True,
      "preview_frames": [
        "131",
        1
      ],
      "preview_fps": 12,
      "tiny_vae": "taeh3.safetensors",
      "model": [
        "178",
        0
      ]
    },
    "class_type": "ModelPreviewOverrideKJ",
    "_meta": {
      "title": "Model Preview Override KJ"
    }
  },
  "147": {
    "inputs": {
      "lora_name": "minimax_h3_ref2v_turbo_8step_v1.0_768p_comfyui_bf16.safetensors",
      "strength_model": 1.0000000000000002,
      "model": [
        "127",
        0
      ]
    },
    "class_type": "LoraLoaderModelOnly",
    "_meta": {
      "title": "Load LoRA"
    }
  },
  "149": {
    "inputs": {
      "shift_video": 12,
      "shift_audio": 3,
      "model": [
        "147",
        0
      ]
    },
    "class_type": "MiniMaxH3SigmaShift",
    "_meta": {
      "title": "ModelSamplingMiniMaxH3"
    }
  },
  "178": {
    "inputs": {
      "attention": "comfy kitchen attention",
      "model": [
        "149",
        0
      ]
    },
    "class_type": "ModelAttentionBackend",
    "_meta": {
      "title": "ModelAttentionBackend"
    }
  },
  "208": {
    "inputs": {
      "step": 6,
      "sigmas": [
        "254",
        0
      ]
    },
    "class_type": "SplitSigmas",
    "_meta": {
      "title": "SplitSigmas"
    }
  },
  "209": {
    "inputs": {
      "noise": [
        "129",
        0
      ],
      "guider": [
        "126",
        0
      ],
      "sampler": [
        "123",
        0
      ],
      "sigmas": [
        "208",
        1
      ],
      "latent_image": [
        "212",
        0
      ]
    },
    "class_type": "SamplerCustomAdvanced",
    "_meta": {
      "title": "SamplerCustomAdvanced"
    }
  },
  "211": {
    "inputs": {
      "av_latent": [
        "125",
        1
      ]
    },
    "class_type": "LTXVSeparateAVLatent",
    "_meta": {
      "title": "Separate AV Latent"
    }
  },
  "212": {
    "inputs": {
      "video_latent": [
        "263",
        0
      ],
      "audio_latent": [
        "211",
        1
      ]
    },
    "class_type": "LTXVConcatAVLatent",
    "_meta": {
      "title": "Concat AV Latent"
    }
  },
  "218": {
    "inputs": {
      "samples": [
        "209",
        0
      ],
      "vae": [
        "120",
        0
      ]
    },
    "class_type": "VAEDecodeAudio",
    "_meta": {
      "title": "VAE Decode Audio"
    }
  },
  "219": {
    "inputs": {
      "samples": [
        "209",
        0
      ],
      "vae": [
        "119",
        0
      ]
    },
    "class_type": "VAEDecode",
    "_meta": {
      "title": "VAE Decode"
    }
  },
  "254": {
    "inputs": {
      "extra_steps": 1,
      "start_at_sigma": 0.7,
      "end_at_sigma": 0,
      "spacing": "cosine",
      "sigmas": [
        "124",
        0
      ]
    },
    "class_type": "H3SigmaRefiner",
    "_meta": {
      "title": "H3 Sigma Refiner"
    }
  },
  "256": {
    "inputs": {
      "image": "07d2e1d22673808899bba100354351b0d4b5b723a10358c7a9ffe92ec0c98ddc.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "257": {
    "inputs": {
      "image": "56a596334282d0057a0847e7a1f2714e8aa27725718b5a162e3ac33c02e42b17.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "258": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "259": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "260": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "263": {
    "inputs": {
      "model_name": "minimax_h3_latent_upscaler_3d_fp16.safetensors",
      "mode": "scale by multiplier",
      "mode.scale": 2,
      "align": 32,
      "device": "cuda",
      "precision": "fp16",
      "enable_chunking": True,
      "latent": [
        "211",
        0
      ]
    },
    "class_type": "MinimaxH3LatentUpscaler3D",
    "_meta": {
      "title": "Minimax H3 Latent Upscaler (3D)"
    }
  },
  "271": {
    "inputs": {
      "frame_rate": 24,
      "loop_count": 0,
      "filename_prefix": "第二次采样",
      "format": "video/h264-mp4",
      "pix_fmt": "yuv420p",
      "crf": 19,
      "save_metadata": True,
      "trim_to_audio": False,
      "pingpong": False,
      "save_output": True,
      "no_preview": False,
      "images": [
        "219",
        0
      ],
      "audio": [
        "218",
        0
      ]
    },
    "class_type": "VHS_VideoCombine",
    "_meta": {
      "title": "Video Combine 🎥🅥🅗🅢"
    }
  },
  "272": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "273": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "274": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "275": {
    "inputs": {
      "audio": "0ea9bca3948a0baf7983804066a8884203e6452b1c37a109bf6e5dc24e616996.flac",
      "audioUI": ""
    },
    "class_type": "LoadAudio",
    "_meta": {
      "title": "Load Audio"
    }
  }
}

# minimax_h3 8张图片加上1个参考音频
minimax_h3_8_image_1_audio_json = {
  "115": {
    "inputs": {
      "aspect_ratio": "16:9 (Widescreen)",
      "megapixels": 0.5,
      "multiple": 32
    },
    "class_type": "ResolutionSelector",
    "_meta": {
      "title": "PASS1 / 16:9 / 0.5MP"
    }
  },
  "119": {
    "inputs": {
      "vae_name": "minimax_h3_video_vae_fp16.safetensors"
    },
    "class_type": "VAELoader",
    "_meta": {
      "title": "Load VAE"
    }
  },
  "120": {
    "inputs": {
      "vae_name": "minimax_h3_audio_vae_fp32.safetensors"
    },
    "class_type": "VAELoader",
    "_meta": {
      "title": "Load VAE"
    }
  },
  "123": {
    "inputs": {
      "sampler_name": "euler"
    },
    "class_type": "KSamplerSelect",
    "_meta": {
      "title": "KSamplerSelect"
    }
  },
  "124": {
    "inputs": {
      "scheduler": "simple",
      "steps": 10,
      "denoise": 1,
      "model": [
        "141",
        0
      ]
    },
    "class_type": "BasicScheduler",
    "_meta": {
      "title": "BasicScheduler"
    }
  },
  "125": {
    "inputs": {
      "noise": [
        "129",
        0
      ],
      "guider": [
        "126",
        0
      ],
      "sampler": [
        "123",
        0
      ],
      "sigmas": [
        "208",
        0
      ],
      "latent_image": [
        "136",
        1
      ]
    },
    "class_type": "SamplerCustomAdvanced",
    "_meta": {
      "title": "SamplerCustomAdvanced"
    }
  },
  "126": {
    "inputs": {
      "model": [
        "141",
        0
      ],
      "conditioning": [
        "136",
        0
      ]
    },
    "class_type": "BasicGuider",
    "_meta": {
      "title": "Basic Guider"
    }
  },
  "127": {
    "inputs": {
      "unet_name": "minimax_h3_hybrid_fl2va_ref2va_b25-49-int8.safetensors",
      "weight_dtype": "default"
    },
    "class_type": "UNETLoader",
    "_meta": {
      "title": "Load Diffusion Model"
    }
  },
  "128": {
    "inputs": {
      "clip_name": "qwen3vl_32b_minimax_h3_int8_convrot.safetensors",
      "type": "minimax",
      "device": "default"
    },
    "class_type": "CLIPLoader",
    "_meta": {
      "title": "Load CLIP"
    }
  },
  "129": {
    "inputs": {
      "noise_seed": 999
    },
    "class_type": "RandomNoise",
    "_meta": {
      "title": "RandomNoise"
    }
  },
  "131": {
    "inputs": {
      "expression": "max(5, round(a * 24)) + (5 - (max(5, round(a * 24)) % 17)) % 17",
      "values.a": [
        "132",
        0
      ]
    },
    "class_type": "ComfyMathExpression",
    "_meta": {
      "title": "Math Expression"
    }
  },
  "132": {
    "inputs": {
      "value": 6
    },
    "class_type": "PrimitiveFloat",
    "_meta": {
      "title": "Float (Duration)"
    }
  },
  "136": {
    "inputs": {
      "prompt": [
        "138",
        0
      ],
      "width": [
        "115",
        0
      ],
      "height": [
        "115",
        1
      ],
      "length": [
        "131",
        1
      ],
      "task_type": "auto",
      "audio_mode": "native",
      "audio_denoise_strength": 1,
      "add_source_as_reference": False,
      "prompt_primary_audio_ordinal": 0,
      "strict_prompt_tags": True,
      "ref_image_size": "match",
      "reference_video_policy": "official_2_to_15s",
      "allow_above_reference_area": True,
      "clip": [
        "128",
        0
      ],
      "video_vae": [
        "119",
        0
      ],
      "audio_vae": [
        "120",
        0
      ],
      "ref_images.ref_image_0": [
        "139",
        0
      ],
      "ref_images.ref_image_1": [
        "256",
        0
      ],
      "ref_images.ref_image_2": [
        "257",
        0
      ],
      "ref_images.ref_image_3": [
        "258",
        0
      ],
      "ref_images.ref_image_4": [
        "259",
        0
      ],
      "ref_images.ref_image_5": [
        "260",
        0
      ],
      "ref_images.ref_image_6": [
        "272",
        0
      ],
      "ref_images.ref_image_7": [
        "273",
        0
      ],
      "ref_audios.ref_audio_0": [
        "275",
        0
      ]
    },
    "class_type": "MiniMaxH3AudioConditioningT8",
    "_meta": {
      "title": "T8 条件节点｜通用模式"
    }
  },
  "138": {
    "inputs": {
      "value": "subject_definitions:\\n<Subject 1> is Lin Che from <Picture 1>, a 29-year-old Chinese woman with a chin-length black bob, a small mole at the outer end of her left eyebrow, a dark red buttoned knitted cardigan over a white crew-neck top and black trousers. Preserve her facial identity, natural skin and wardrobe; the three standing views do not dictate her seated performance.\\n<Subject 2> is Chen Li from <Picture 2>, a 48-year-old Chinese man with a square face, short black hair graying at the temples, a slight gap in his right eyebrow, a medium-gray knitted cardigan over a pale blue shirt and dark gray trousers. Preserve his face, age, hair and clothing, not the reference pose.\\n<Subject 3> is the same empty meeting room from <Picture 3>: a matte light-gray rectangular table with its long axis east-west, one chair at each east and west short end, a closed high frosted window in the north wall, a low dark-green six-cubby cabinet against the west wall and a closed brown door in the south wall. Preserve the world-space layout and matte surfaces. Omit the four-view borders, reference viewpoints and incidental objects; the room contains only the two directed people and the one directed recorder.\\n\\nsummary:\\n[reference generation] A 6-second continuous live-action medium shot in <Subject 3>. Lin Che establishes that the recorder is already running and challenges Chen Li to speak on record. The three pictures supply identity and room design, with newly directed framing rather than exact endpoints.\\n\\nretention_analysis:\\n<Subject 1> (appears in [Shot 1]): fully_preserved - Keep Lin Che's identity, bob, dark red cardigan and white inner top while directing the specified seated performance.\\n<Subject 2> (appears in [Shot 1]): fully_preserved - Keep Chen Li's identity, gray temples, gray cardigan and pale blue shirt; the directed seated pose replaces the standing reference.\\n<Subject 3> (appears in [Shot 1]): partially_preserved - Keep the fixed room topology, north-window light, west cabinet and table material; omit multi-view panels and reference framing. The initial camera composition is newly directed.\\n\\ndetailed_description:\\nThe target video is a restrained contemporary Chinese live-action suspense drama, with natural skin texture, readable faces and softly lit matte surfaces.\\n[Shot 1] The camera occupies the open southeast aisle at approximately (1.5,-1.5,1.3) meters relative to the table center and faces northwest toward <Subject 1>. She is seated at the west end on screen-left, torso and head turned east toward <Subject 2>, with her gaze going screen-right. Her chin-length bob, natural eyebrow mark and dark red cardigan remain visible. His gray-clad shoulder and pale blue collar occupy only the extreme right foreground; his body remains at the east seat, and his shoulder does not obscure her face, hands or the recorder. The background shows the west green cabinet and only a geometrically plausible part of the north wall and window. The south door stays behind the camera and out of frame.\\nBoth remain seated on the same two chairs, feet on the floor, with neither changing seats or turning away. <Subject 1>'s two empty hands rest separately on the west table edge; <Subject 2>'s left hand rests on the east edge. There is exactly one small black rectangular audio recorder, about 10 by 3 by 1 centimeters, lying flat on the matte tabletop, long axis east-west and its single red indicator steadily lit. It has no readable display. Its center is 0.35 meters east and 0.12 meters south of the table center. His right fingertips rest on the tabletop three centimeters east of the recorder, separated from its casing. The recorder and both hands remain still until any explicitly directed action.\\nHold the initial pose for about one second. <Subject 1> (S1), using a clear low young-adult female Mandarin voice, measured and direct, says <d>[Chinese] 录音开着。你还要我关掉？</d> The statement about recording is a condition of this conversation, not a command to press a button. Finish speaking by about 4.5 seconds, close the mouth and hold eye contact for the remaining beat. Only speech-related lips, small facial tension and natural breathing change. The listener keeps a closed mouth and still hands. No control is pressed, and the indicator remains steadily red.\\nThe sole key is diffused cool-neutral daylight from the fixed high north window, above seated eye level. It softly illuminates the north-facing cheek, the upper knuckles and the recorder's top plane. Weak, slightly warm bounce from the south wall preserves detail on the shadow side without creating another hard shadow. Hair casts a gentle edge at the jaw, and sleeves retain soft folds. Small contact shadows attach hands and the recorder to the tabletop and extend toward the south in world space; the stationary recorder retains a stationary contact shadow. Keep source positions, exposure and white balance steady. Matte surfaces produce subdued highlights rather than flashes. Changing the viewpoint must not relocate the light to the camera side.\\nUse a 40 mm-equivalent lens at seated eye height, in a medium composition with enough depth of field for the featured face, hands and recorder to remain legible. Focus stays on the featured person's eyes without a focus pull. The camera remains fixed throughout; position, orientation, focal length and framing stay unchanged. The foreground shoulder remains a narrow edge element, not a moving wipe or obstruction. Keep the same single shot from beginning to end.\\nThe output is one full-frame scene, with no reference panels, additional people, automatic captions or decorative overlays. Preserve the settled end pose for the adjacent reverse-angle cut.\\n\\noverall_soundscape:\\nLow steady ventilation and distant, muffled room ambience, with subtle breaths and fabric noise. The stationary recorder produces no playback, beeps or repeated scrape. Keep the room tone unobtrusive beneath the voice.\\n\\nnon_diegetic_music:\\nN/A"
    },
    "class_type": "PrimitiveStringMultiline",
    "_meta": {
      "title": "Input Text (Prompt)"
    }
  },
  "139": {
    "inputs": {
      "image": "2636c786c4c0e6c33db28ba14bbe1c381ed4f7cbd8ae925b745e370640e55fea.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "141": {
    "inputs": {
      "max_resolution": 1024,
      "jpeg_quality": 80,
      "suppress_default_preview": True,
      "preview_frames": [
        "131",
        1
      ],
      "preview_fps": 12,
      "tiny_vae": "taeh3.safetensors",
      "model": [
        "178",
        0
      ]
    },
    "class_type": "ModelPreviewOverrideKJ",
    "_meta": {
      "title": "Model Preview Override KJ"
    }
  },
  "147": {
    "inputs": {
      "lora_name": "minimax_h3_ref2v_turbo_8step_v1.0_768p_comfyui_bf16.safetensors",
      "strength_model": 1.0000000000000002,
      "model": [
        "127",
        0
      ]
    },
    "class_type": "LoraLoaderModelOnly",
    "_meta": {
      "title": "Load LoRA"
    }
  },
  "149": {
    "inputs": {
      "shift_video": 12,
      "shift_audio": 3,
      "model": [
        "147",
        0
      ]
    },
    "class_type": "MiniMaxH3SigmaShift",
    "_meta": {
      "title": "ModelSamplingMiniMaxH3"
    }
  },
  "178": {
    "inputs": {
      "attention": "comfy kitchen attention",
      "model": [
        "149",
        0
      ]
    },
    "class_type": "ModelAttentionBackend",
    "_meta": {
      "title": "ModelAttentionBackend"
    }
  },
  "208": {
    "inputs": {
      "step": 6,
      "sigmas": [
        "254",
        0
      ]
    },
    "class_type": "SplitSigmas",
    "_meta": {
      "title": "SplitSigmas"
    }
  },
  "209": {
    "inputs": {
      "noise": [
        "129",
        0
      ],
      "guider": [
        "126",
        0
      ],
      "sampler": [
        "123",
        0
      ],
      "sigmas": [
        "208",
        1
      ],
      "latent_image": [
        "212",
        0
      ]
    },
    "class_type": "SamplerCustomAdvanced",
    "_meta": {
      "title": "SamplerCustomAdvanced"
    }
  },
  "211": {
    "inputs": {
      "av_latent": [
        "125",
        1
      ]
    },
    "class_type": "LTXVSeparateAVLatent",
    "_meta": {
      "title": "Separate AV Latent"
    }
  },
  "212": {
    "inputs": {
      "video_latent": [
        "263",
        0
      ],
      "audio_latent": [
        "211",
        1
      ]
    },
    "class_type": "LTXVConcatAVLatent",
    "_meta": {
      "title": "Concat AV Latent"
    }
  },
  "218": {
    "inputs": {
      "samples": [
        "209",
        0
      ],
      "vae": [
        "120",
        0
      ]
    },
    "class_type": "VAEDecodeAudio",
    "_meta": {
      "title": "VAE Decode Audio"
    }
  },
  "219": {
    "inputs": {
      "samples": [
        "209",
        0
      ],
      "vae": [
        "119",
        0
      ]
    },
    "class_type": "VAEDecode",
    "_meta": {
      "title": "VAE Decode"
    }
  },
  "254": {
    "inputs": {
      "extra_steps": 1,
      "start_at_sigma": 0.7,
      "end_at_sigma": 0,
      "spacing": "cosine",
      "sigmas": [
        "124",
        0
      ]
    },
    "class_type": "H3SigmaRefiner",
    "_meta": {
      "title": "H3 Sigma Refiner"
    }
  },
  "256": {
    "inputs": {
      "image": "07d2e1d22673808899bba100354351b0d4b5b723a10358c7a9ffe92ec0c98ddc.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "257": {
    "inputs": {
      "image": "56a596334282d0057a0847e7a1f2714e8aa27725718b5a162e3ac33c02e42b17.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "258": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "259": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "260": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "263": {
    "inputs": {
      "model_name": "minimax_h3_latent_upscaler_3d_fp16.safetensors",
      "mode": "scale by multiplier",
      "mode.scale": 2,
      "align": 32,
      "device": "cuda",
      "precision": "fp16",
      "enable_chunking": True,
      "latent": [
        "211",
        0
      ]
    },
    "class_type": "MinimaxH3LatentUpscaler3D",
    "_meta": {
      "title": "Minimax H3 Latent Upscaler (3D)"
    }
  },
  "271": {
    "inputs": {
      "frame_rate": 24,
      "loop_count": 0,
      "filename_prefix": "第二次采样",
      "format": "video/h264-mp4",
      "pix_fmt": "yuv420p",
      "crf": 19,
      "save_metadata": True,
      "trim_to_audio": False,
      "pingpong": False,
      "save_output": True,
      "no_preview": False,
      "images": [
        "219",
        0
      ],
      "audio": [
        "218",
        0
      ]
    },
    "class_type": "VHS_VideoCombine",
    "_meta": {
      "title": "Video Combine 🎥🅥🅗🅢"
    }
  },
  "272": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "273": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "274": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "275": {
    "inputs": {
      "audio": "0ea9bca3948a0baf7983804066a8884203e6452b1c37a109bf6e5dc24e616996.flac",
      "audioUI": ""
    },
    "class_type": "LoadAudio",
    "_meta": {
      "title": "Load Audio"
    }
  }
}

# minimax_h3 7张图片加上1个参考音频
minimax_h3_7_image_1_audio_json = {
  "115": {
    "inputs": {
      "aspect_ratio": "16:9 (Widescreen)",
      "megapixels": 0.5,
      "multiple": 32
    },
    "class_type": "ResolutionSelector",
    "_meta": {
      "title": "PASS1 / 16:9 / 0.5MP"
    }
  },
  "119": {
    "inputs": {
      "vae_name": "minimax_h3_video_vae_fp16.safetensors"
    },
    "class_type": "VAELoader",
    "_meta": {
      "title": "Load VAE"
    }
  },
  "120": {
    "inputs": {
      "vae_name": "minimax_h3_audio_vae_fp32.safetensors"
    },
    "class_type": "VAELoader",
    "_meta": {
      "title": "Load VAE"
    }
  },
  "123": {
    "inputs": {
      "sampler_name": "euler"
    },
    "class_type": "KSamplerSelect",
    "_meta": {
      "title": "KSamplerSelect"
    }
  },
  "124": {
    "inputs": {
      "scheduler": "simple",
      "steps": 10,
      "denoise": 1,
      "model": [
        "141",
        0
      ]
    },
    "class_type": "BasicScheduler",
    "_meta": {
      "title": "BasicScheduler"
    }
  },
  "125": {
    "inputs": {
      "noise": [
        "129",
        0
      ],
      "guider": [
        "126",
        0
      ],
      "sampler": [
        "123",
        0
      ],
      "sigmas": [
        "208",
        0
      ],
      "latent_image": [
        "136",
        1
      ]
    },
    "class_type": "SamplerCustomAdvanced",
    "_meta": {
      "title": "SamplerCustomAdvanced"
    }
  },
  "126": {
    "inputs": {
      "model": [
        "141",
        0
      ],
      "conditioning": [
        "136",
        0
      ]
    },
    "class_type": "BasicGuider",
    "_meta": {
      "title": "Basic Guider"
    }
  },
  "127": {
    "inputs": {
      "unet_name": "minimax_h3_hybrid_fl2va_ref2va_b25-49-int8.safetensors",
      "weight_dtype": "default"
    },
    "class_type": "UNETLoader",
    "_meta": {
      "title": "Load Diffusion Model"
    }
  },
  "128": {
    "inputs": {
      "clip_name": "qwen3vl_32b_minimax_h3_int8_convrot.safetensors",
      "type": "minimax",
      "device": "default"
    },
    "class_type": "CLIPLoader",
    "_meta": {
      "title": "Load CLIP"
    }
  },
  "129": {
    "inputs": {
      "noise_seed": 999
    },
    "class_type": "RandomNoise",
    "_meta": {
      "title": "RandomNoise"
    }
  },
  "131": {
    "inputs": {
      "expression": "max(5, round(a * 24)) + (5 - (max(5, round(a * 24)) % 17)) % 17",
      "values.a": [
        "132",
        0
      ]
    },
    "class_type": "ComfyMathExpression",
    "_meta": {
      "title": "Math Expression"
    }
  },
  "132": {
    "inputs": {
      "value": 6
    },
    "class_type": "PrimitiveFloat",
    "_meta": {
      "title": "Float (Duration)"
    }
  },
  "136": {
    "inputs": {
      "prompt": [
        "138",
        0
      ],
      "width": [
        "115",
        0
      ],
      "height": [
        "115",
        1
      ],
      "length": [
        "131",
        1
      ],
      "task_type": "auto",
      "audio_mode": "native",
      "audio_denoise_strength": 1,
      "add_source_as_reference": False,
      "prompt_primary_audio_ordinal": 0,
      "strict_prompt_tags": True,
      "ref_image_size": "match",
      "reference_video_policy": "official_2_to_15s",
      "allow_above_reference_area": True,
      "clip": [
        "128",
        0
      ],
      "video_vae": [
        "119",
        0
      ],
      "audio_vae": [
        "120",
        0
      ],
      "ref_images.ref_image_0": [
        "139",
        0
      ],
      "ref_images.ref_image_1": [
        "256",
        0
      ],
      "ref_images.ref_image_2": [
        "257",
        0
      ],
      "ref_images.ref_image_3": [
        "258",
        0
      ],
      "ref_images.ref_image_4": [
        "259",
        0
      ],
      "ref_images.ref_image_5": [
        "260",
        0
      ],
      "ref_images.ref_image_6": [
        "272",
        0
      ],
      "ref_audios.ref_audio_0": [
        "275",
        0
      ]
    },
    "class_type": "MiniMaxH3AudioConditioningT8",
    "_meta": {
      "title": "T8 条件节点｜通用模式"
    }
  },
  "138": {
    "inputs": {
      "value": "subject_definitions:\\n<Subject 1> is Lin Che from <Picture 1>, a 29-year-old Chinese woman with a chin-length black bob, a small mole at the outer end of her left eyebrow, a dark red buttoned knitted cardigan over a white crew-neck top and black trousers. Preserve her facial identity, natural skin and wardrobe; the three standing views do not dictate her seated performance.\\n<Subject 2> is Chen Li from <Picture 2>, a 48-year-old Chinese man with a square face, short black hair graying at the temples, a slight gap in his right eyebrow, a medium-gray knitted cardigan over a pale blue shirt and dark gray trousers. Preserve his face, age, hair and clothing, not the reference pose.\\n<Subject 3> is the same empty meeting room from <Picture 3>: a matte light-gray rectangular table with its long axis east-west, one chair at each east and west short end, a closed high frosted window in the north wall, a low dark-green six-cubby cabinet against the west wall and a closed brown door in the south wall. Preserve the world-space layout and matte surfaces. Omit the four-view borders, reference viewpoints and incidental objects; the room contains only the two directed people and the one directed recorder.\\n\\nsummary:\\n[reference generation] A 6-second continuous live-action medium shot in <Subject 3>. Lin Che establishes that the recorder is already running and challenges Chen Li to speak on record. The three pictures supply identity and room design, with newly directed framing rather than exact endpoints.\\n\\nretention_analysis:\\n<Subject 1> (appears in [Shot 1]): fully_preserved - Keep Lin Che's identity, bob, dark red cardigan and white inner top while directing the specified seated performance.\\n<Subject 2> (appears in [Shot 1]): fully_preserved - Keep Chen Li's identity, gray temples, gray cardigan and pale blue shirt; the directed seated pose replaces the standing reference.\\n<Subject 3> (appears in [Shot 1]): partially_preserved - Keep the fixed room topology, north-window light, west cabinet and table material; omit multi-view panels and reference framing. The initial camera composition is newly directed.\\n\\ndetailed_description:\\nThe target video is a restrained contemporary Chinese live-action suspense drama, with natural skin texture, readable faces and softly lit matte surfaces.\\n[Shot 1] The camera occupies the open southeast aisle at approximately (1.5,-1.5,1.3) meters relative to the table center and faces northwest toward <Subject 1>. She is seated at the west end on screen-left, torso and head turned east toward <Subject 2>, with her gaze going screen-right. Her chin-length bob, natural eyebrow mark and dark red cardigan remain visible. His gray-clad shoulder and pale blue collar occupy only the extreme right foreground; his body remains at the east seat, and his shoulder does not obscure her face, hands or the recorder. The background shows the west green cabinet and only a geometrically plausible part of the north wall and window. The south door stays behind the camera and out of frame.\\nBoth remain seated on the same two chairs, feet on the floor, with neither changing seats or turning away. <Subject 1>'s two empty hands rest separately on the west table edge; <Subject 2>'s left hand rests on the east edge. There is exactly one small black rectangular audio recorder, about 10 by 3 by 1 centimeters, lying flat on the matte tabletop, long axis east-west and its single red indicator steadily lit. It has no readable display. Its center is 0.35 meters east and 0.12 meters south of the table center. His right fingertips rest on the tabletop three centimeters east of the recorder, separated from its casing. The recorder and both hands remain still until any explicitly directed action.\\nHold the initial pose for about one second. <Subject 1> (S1), using a clear low young-adult female Mandarin voice, measured and direct, says <d>[Chinese] 录音开着。你还要我关掉？</d> The statement about recording is a condition of this conversation, not a command to press a button. Finish speaking by about 4.5 seconds, close the mouth and hold eye contact for the remaining beat. Only speech-related lips, small facial tension and natural breathing change. The listener keeps a closed mouth and still hands. No control is pressed, and the indicator remains steadily red.\\nThe sole key is diffused cool-neutral daylight from the fixed high north window, above seated eye level. It softly illuminates the north-facing cheek, the upper knuckles and the recorder's top plane. Weak, slightly warm bounce from the south wall preserves detail on the shadow side without creating another hard shadow. Hair casts a gentle edge at the jaw, and sleeves retain soft folds. Small contact shadows attach hands and the recorder to the tabletop and extend toward the south in world space; the stationary recorder retains a stationary contact shadow. Keep source positions, exposure and white balance steady. Matte surfaces produce subdued highlights rather than flashes. Changing the viewpoint must not relocate the light to the camera side.\\nUse a 40 mm-equivalent lens at seated eye height, in a medium composition with enough depth of field for the featured face, hands and recorder to remain legible. Focus stays on the featured person's eyes without a focus pull. The camera remains fixed throughout; position, orientation, focal length and framing stay unchanged. The foreground shoulder remains a narrow edge element, not a moving wipe or obstruction. Keep the same single shot from beginning to end.\\nThe output is one full-frame scene, with no reference panels, additional people, automatic captions or decorative overlays. Preserve the settled end pose for the adjacent reverse-angle cut.\\n\\noverall_soundscape:\\nLow steady ventilation and distant, muffled room ambience, with subtle breaths and fabric noise. The stationary recorder produces no playback, beeps or repeated scrape. Keep the room tone unobtrusive beneath the voice.\\n\\nnon_diegetic_music:\\nN/A"
    },
    "class_type": "PrimitiveStringMultiline",
    "_meta": {
      "title": "Input Text (Prompt)"
    }
  },
  "139": {
    "inputs": {
      "image": "2636c786c4c0e6c33db28ba14bbe1c381ed4f7cbd8ae925b745e370640e55fea.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "141": {
    "inputs": {
      "max_resolution": 1024,
      "jpeg_quality": 80,
      "suppress_default_preview": True,
      "preview_frames": [
        "131",
        1
      ],
      "preview_fps": 12,
      "tiny_vae": "taeh3.safetensors",
      "model": [
        "178",
        0
      ]
    },
    "class_type": "ModelPreviewOverrideKJ",
    "_meta": {
      "title": "Model Preview Override KJ"
    }
  },
  "147": {
    "inputs": {
      "lora_name": "minimax_h3_ref2v_turbo_8step_v1.0_768p_comfyui_bf16.safetensors",
      "strength_model": 1.0000000000000002,
      "model": [
        "127",
        0
      ]
    },
    "class_type": "LoraLoaderModelOnly",
    "_meta": {
      "title": "Load LoRA"
    }
  },
  "149": {
    "inputs": {
      "shift_video": 12,
      "shift_audio": 3,
      "model": [
        "147",
        0
      ]
    },
    "class_type": "MiniMaxH3SigmaShift",
    "_meta": {
      "title": "ModelSamplingMiniMaxH3"
    }
  },
  "178": {
    "inputs": {
      "attention": "comfy kitchen attention",
      "model": [
        "149",
        0
      ]
    },
    "class_type": "ModelAttentionBackend",
    "_meta": {
      "title": "ModelAttentionBackend"
    }
  },
  "208": {
    "inputs": {
      "step": 6,
      "sigmas": [
        "254",
        0
      ]
    },
    "class_type": "SplitSigmas",
    "_meta": {
      "title": "SplitSigmas"
    }
  },
  "209": {
    "inputs": {
      "noise": [
        "129",
        0
      ],
      "guider": [
        "126",
        0
      ],
      "sampler": [
        "123",
        0
      ],
      "sigmas": [
        "208",
        1
      ],
      "latent_image": [
        "212",
        0
      ]
    },
    "class_type": "SamplerCustomAdvanced",
    "_meta": {
      "title": "SamplerCustomAdvanced"
    }
  },
  "211": {
    "inputs": {
      "av_latent": [
        "125",
        1
      ]
    },
    "class_type": "LTXVSeparateAVLatent",
    "_meta": {
      "title": "Separate AV Latent"
    }
  },
  "212": {
    "inputs": {
      "video_latent": [
        "263",
        0
      ],
      "audio_latent": [
        "211",
        1
      ]
    },
    "class_type": "LTXVConcatAVLatent",
    "_meta": {
      "title": "Concat AV Latent"
    }
  },
  "218": {
    "inputs": {
      "samples": [
        "209",
        0
      ],
      "vae": [
        "120",
        0
      ]
    },
    "class_type": "VAEDecodeAudio",
    "_meta": {
      "title": "VAE Decode Audio"
    }
  },
  "219": {
    "inputs": {
      "samples": [
        "209",
        0
      ],
      "vae": [
        "119",
        0
      ]
    },
    "class_type": "VAEDecode",
    "_meta": {
      "title": "VAE Decode"
    }
  },
  "254": {
    "inputs": {
      "extra_steps": 1,
      "start_at_sigma": 0.7,
      "end_at_sigma": 0,
      "spacing": "cosine",
      "sigmas": [
        "124",
        0
      ]
    },
    "class_type": "H3SigmaRefiner",
    "_meta": {
      "title": "H3 Sigma Refiner"
    }
  },
  "256": {
    "inputs": {
      "image": "07d2e1d22673808899bba100354351b0d4b5b723a10358c7a9ffe92ec0c98ddc.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "257": {
    "inputs": {
      "image": "56a596334282d0057a0847e7a1f2714e8aa27725718b5a162e3ac33c02e42b17.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "258": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "259": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "260": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "263": {
    "inputs": {
      "model_name": "minimax_h3_latent_upscaler_3d_fp16.safetensors",
      "mode": "scale by multiplier",
      "mode.scale": 2,
      "align": 32,
      "device": "cuda",
      "precision": "fp16",
      "enable_chunking": True,
      "latent": [
        "211",
        0
      ]
    },
    "class_type": "MinimaxH3LatentUpscaler3D",
    "_meta": {
      "title": "Minimax H3 Latent Upscaler (3D)"
    }
  },
  "271": {
    "inputs": {
      "frame_rate": 24,
      "loop_count": 0,
      "filename_prefix": "第二次采样",
      "format": "video/h264-mp4",
      "pix_fmt": "yuv420p",
      "crf": 19,
      "save_metadata": True,
      "trim_to_audio": False,
      "pingpong": False,
      "save_output": True,
      "no_preview": False,
      "images": [
        "219",
        0
      ],
      "audio": [
        "218",
        0
      ]
    },
    "class_type": "VHS_VideoCombine",
    "_meta": {
      "title": "Video Combine 🎥🅥🅗🅢"
    }
  },
  "272": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "273": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "274": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "275": {
    "inputs": {
      "audio": "0ea9bca3948a0baf7983804066a8884203e6452b1c37a109bf6e5dc24e616996.flac",
      "audioUI": ""
    },
    "class_type": "LoadAudio",
    "_meta": {
      "title": "Load Audio"
    }
  }
}

# minimax_h3 6张图片加上1个参考音频
minimax_h3_6_image_1_audio_json = {
  "115": {
    "inputs": {
      "aspect_ratio": "16:9 (Widescreen)",
      "megapixels": 0.5,
      "multiple": 32
    },
    "class_type": "ResolutionSelector",
    "_meta": {
      "title": "PASS1 / 16:9 / 0.5MP"
    }
  },
  "119": {
    "inputs": {
      "vae_name": "minimax_h3_video_vae_fp16.safetensors"
    },
    "class_type": "VAELoader",
    "_meta": {
      "title": "Load VAE"
    }
  },
  "120": {
    "inputs": {
      "vae_name": "minimax_h3_audio_vae_fp32.safetensors"
    },
    "class_type": "VAELoader",
    "_meta": {
      "title": "Load VAE"
    }
  },
  "123": {
    "inputs": {
      "sampler_name": "euler"
    },
    "class_type": "KSamplerSelect",
    "_meta": {
      "title": "KSamplerSelect"
    }
  },
  "124": {
    "inputs": {
      "scheduler": "simple",
      "steps": 10,
      "denoise": 1,
      "model": [
        "141",
        0
      ]
    },
    "class_type": "BasicScheduler",
    "_meta": {
      "title": "BasicScheduler"
    }
  },
  "125": {
    "inputs": {
      "noise": [
        "129",
        0
      ],
      "guider": [
        "126",
        0
      ],
      "sampler": [
        "123",
        0
      ],
      "sigmas": [
        "208",
        0
      ],
      "latent_image": [
        "136",
        1
      ]
    },
    "class_type": "SamplerCustomAdvanced",
    "_meta": {
      "title": "SamplerCustomAdvanced"
    }
  },
  "126": {
    "inputs": {
      "model": [
        "141",
        0
      ],
      "conditioning": [
        "136",
        0
      ]
    },
    "class_type": "BasicGuider",
    "_meta": {
      "title": "Basic Guider"
    }
  },
  "127": {
    "inputs": {
      "unet_name": "minimax_h3_hybrid_fl2va_ref2va_b25-49-int8.safetensors",
      "weight_dtype": "default"
    },
    "class_type": "UNETLoader",
    "_meta": {
      "title": "Load Diffusion Model"
    }
  },
  "128": {
    "inputs": {
      "clip_name": "qwen3vl_32b_minimax_h3_int8_convrot.safetensors",
      "type": "minimax",
      "device": "default"
    },
    "class_type": "CLIPLoader",
    "_meta": {
      "title": "Load CLIP"
    }
  },
  "129": {
    "inputs": {
      "noise_seed": 999
    },
    "class_type": "RandomNoise",
    "_meta": {
      "title": "RandomNoise"
    }
  },
  "131": {
    "inputs": {
      "expression": "max(5, round(a * 24)) + (5 - (max(5, round(a * 24)) % 17)) % 17",
      "values.a": [
        "132",
        0
      ]
    },
    "class_type": "ComfyMathExpression",
    "_meta": {
      "title": "Math Expression"
    }
  },
  "132": {
    "inputs": {
      "value": 6
    },
    "class_type": "PrimitiveFloat",
    "_meta": {
      "title": "Float (Duration)"
    }
  },
  "136": {
    "inputs": {
      "prompt": [
        "138",
        0
      ],
      "width": [
        "115",
        0
      ],
      "height": [
        "115",
        1
      ],
      "length": [
        "131",
        1
      ],
      "task_type": "auto",
      "audio_mode": "native",
      "audio_denoise_strength": 1,
      "add_source_as_reference": False,
      "prompt_primary_audio_ordinal": 0,
      "strict_prompt_tags": True,
      "ref_image_size": "match",
      "reference_video_policy": "official_2_to_15s",
      "allow_above_reference_area": True,
      "clip": [
        "128",
        0
      ],
      "video_vae": [
        "119",
        0
      ],
      "audio_vae": [
        "120",
        0
      ],
      "ref_images.ref_image_0": [
        "139",
        0
      ],
      "ref_images.ref_image_1": [
        "256",
        0
      ],
      "ref_images.ref_image_2": [
        "257",
        0
      ],
      "ref_images.ref_image_3": [
        "258",
        0
      ],
      "ref_images.ref_image_4": [
        "259",
        0
      ],
      "ref_images.ref_image_5": [
        "260",
        0
      ],
      "ref_audios.ref_audio_0": [
        "275",
        0
      ]
    },
    "class_type": "MiniMaxH3AudioConditioningT8",
    "_meta": {
      "title": "T8 条件节点｜通用模式"
    }
  },
  "138": {
    "inputs": {
      "value": "subject_definitions:\\n<Subject 1> is Lin Che from <Picture 1>, a 29-year-old Chinese woman with a chin-length black bob, a small mole at the outer end of her left eyebrow, a dark red buttoned knitted cardigan over a white crew-neck top and black trousers. Preserve her facial identity, natural skin and wardrobe; the three standing views do not dictate her seated performance.\\n<Subject 2> is Chen Li from <Picture 2>, a 48-year-old Chinese man with a square face, short black hair graying at the temples, a slight gap in his right eyebrow, a medium-gray knitted cardigan over a pale blue shirt and dark gray trousers. Preserve his face, age, hair and clothing, not the reference pose.\\n<Subject 3> is the same empty meeting room from <Picture 3>: a matte light-gray rectangular table with its long axis east-west, one chair at each east and west short end, a closed high frosted window in the north wall, a low dark-green six-cubby cabinet against the west wall and a closed brown door in the south wall. Preserve the world-space layout and matte surfaces. Omit the four-view borders, reference viewpoints and incidental objects; the room contains only the two directed people and the one directed recorder.\\n\\nsummary:\\n[reference generation] A 6-second continuous live-action medium shot in <Subject 3>. Lin Che establishes that the recorder is already running and challenges Chen Li to speak on record. The three pictures supply identity and room design, with newly directed framing rather than exact endpoints.\\n\\nretention_analysis:\\n<Subject 1> (appears in [Shot 1]): fully_preserved - Keep Lin Che's identity, bob, dark red cardigan and white inner top while directing the specified seated performance.\\n<Subject 2> (appears in [Shot 1]): fully_preserved - Keep Chen Li's identity, gray temples, gray cardigan and pale blue shirt; the directed seated pose replaces the standing reference.\\n<Subject 3> (appears in [Shot 1]): partially_preserved - Keep the fixed room topology, north-window light, west cabinet and table material; omit multi-view panels and reference framing. The initial camera composition is newly directed.\\n\\ndetailed_description:\\nThe target video is a restrained contemporary Chinese live-action suspense drama, with natural skin texture, readable faces and softly lit matte surfaces.\\n[Shot 1] The camera occupies the open southeast aisle at approximately (1.5,-1.5,1.3) meters relative to the table center and faces northwest toward <Subject 1>. She is seated at the west end on screen-left, torso and head turned east toward <Subject 2>, with her gaze going screen-right. Her chin-length bob, natural eyebrow mark and dark red cardigan remain visible. His gray-clad shoulder and pale blue collar occupy only the extreme right foreground; his body remains at the east seat, and his shoulder does not obscure her face, hands or the recorder. The background shows the west green cabinet and only a geometrically plausible part of the north wall and window. The south door stays behind the camera and out of frame.\\nBoth remain seated on the same two chairs, feet on the floor, with neither changing seats or turning away. <Subject 1>'s two empty hands rest separately on the west table edge; <Subject 2>'s left hand rests on the east edge. There is exactly one small black rectangular audio recorder, about 10 by 3 by 1 centimeters, lying flat on the matte tabletop, long axis east-west and its single red indicator steadily lit. It has no readable display. Its center is 0.35 meters east and 0.12 meters south of the table center. His right fingertips rest on the tabletop three centimeters east of the recorder, separated from its casing. The recorder and both hands remain still until any explicitly directed action.\\nHold the initial pose for about one second. <Subject 1> (S1), using a clear low young-adult female Mandarin voice, measured and direct, says <d>[Chinese] 录音开着。你还要我关掉？</d> The statement about recording is a condition of this conversation, not a command to press a button. Finish speaking by about 4.5 seconds, close the mouth and hold eye contact for the remaining beat. Only speech-related lips, small facial tension and natural breathing change. The listener keeps a closed mouth and still hands. No control is pressed, and the indicator remains steadily red.\\nThe sole key is diffused cool-neutral daylight from the fixed high north window, above seated eye level. It softly illuminates the north-facing cheek, the upper knuckles and the recorder's top plane. Weak, slightly warm bounce from the south wall preserves detail on the shadow side without creating another hard shadow. Hair casts a gentle edge at the jaw, and sleeves retain soft folds. Small contact shadows attach hands and the recorder to the tabletop and extend toward the south in world space; the stationary recorder retains a stationary contact shadow. Keep source positions, exposure and white balance steady. Matte surfaces produce subdued highlights rather than flashes. Changing the viewpoint must not relocate the light to the camera side.\\nUse a 40 mm-equivalent lens at seated eye height, in a medium composition with enough depth of field for the featured face, hands and recorder to remain legible. Focus stays on the featured person's eyes without a focus pull. The camera remains fixed throughout; position, orientation, focal length and framing stay unchanged. The foreground shoulder remains a narrow edge element, not a moving wipe or obstruction. Keep the same single shot from beginning to end.\\nThe output is one full-frame scene, with no reference panels, additional people, automatic captions or decorative overlays. Preserve the settled end pose for the adjacent reverse-angle cut.\\n\\noverall_soundscape:\\nLow steady ventilation and distant, muffled room ambience, with subtle breaths and fabric noise. The stationary recorder produces no playback, beeps or repeated scrape. Keep the room tone unobtrusive beneath the voice.\\n\\nnon_diegetic_music:\\nN/A"
    },
    "class_type": "PrimitiveStringMultiline",
    "_meta": {
      "title": "Input Text (Prompt)"
    }
  },
  "139": {
    "inputs": {
      "image": "2636c786c4c0e6c33db28ba14bbe1c381ed4f7cbd8ae925b745e370640e55fea.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "141": {
    "inputs": {
      "max_resolution": 1024,
      "jpeg_quality": 80,
      "suppress_default_preview": True,
      "preview_frames": [
        "131",
        1
      ],
      "preview_fps": 12,
      "tiny_vae": "taeh3.safetensors",
      "model": [
        "178",
        0
      ]
    },
    "class_type": "ModelPreviewOverrideKJ",
    "_meta": {
      "title": "Model Preview Override KJ"
    }
  },
  "147": {
    "inputs": {
      "lora_name": "minimax_h3_ref2v_turbo_8step_v1.0_768p_comfyui_bf16.safetensors",
      "strength_model": 1.0000000000000002,
      "model": [
        "127",
        0
      ]
    },
    "class_type": "LoraLoaderModelOnly",
    "_meta": {
      "title": "Load LoRA"
    }
  },
  "149": {
    "inputs": {
      "shift_video": 12,
      "shift_audio": 3,
      "model": [
        "147",
        0
      ]
    },
    "class_type": "MiniMaxH3SigmaShift",
    "_meta": {
      "title": "ModelSamplingMiniMaxH3"
    }
  },
  "178": {
    "inputs": {
      "attention": "comfy kitchen attention",
      "model": [
        "149",
        0
      ]
    },
    "class_type": "ModelAttentionBackend",
    "_meta": {
      "title": "ModelAttentionBackend"
    }
  },
  "208": {
    "inputs": {
      "step": 6,
      "sigmas": [
        "254",
        0
      ]
    },
    "class_type": "SplitSigmas",
    "_meta": {
      "title": "SplitSigmas"
    }
  },
  "209": {
    "inputs": {
      "noise": [
        "129",
        0
      ],
      "guider": [
        "126",
        0
      ],
      "sampler": [
        "123",
        0
      ],
      "sigmas": [
        "208",
        1
      ],
      "latent_image": [
        "212",
        0
      ]
    },
    "class_type": "SamplerCustomAdvanced",
    "_meta": {
      "title": "SamplerCustomAdvanced"
    }
  },
  "211": {
    "inputs": {
      "av_latent": [
        "125",
        1
      ]
    },
    "class_type": "LTXVSeparateAVLatent",
    "_meta": {
      "title": "Separate AV Latent"
    }
  },
  "212": {
    "inputs": {
      "video_latent": [
        "263",
        0
      ],
      "audio_latent": [
        "211",
        1
      ]
    },
    "class_type": "LTXVConcatAVLatent",
    "_meta": {
      "title": "Concat AV Latent"
    }
  },
  "218": {
    "inputs": {
      "samples": [
        "209",
        0
      ],
      "vae": [
        "120",
        0
      ]
    },
    "class_type": "VAEDecodeAudio",
    "_meta": {
      "title": "VAE Decode Audio"
    }
  },
  "219": {
    "inputs": {
      "samples": [
        "209",
        0
      ],
      "vae": [
        "119",
        0
      ]
    },
    "class_type": "VAEDecode",
    "_meta": {
      "title": "VAE Decode"
    }
  },
  "254": {
    "inputs": {
      "extra_steps": 1,
      "start_at_sigma": 0.7,
      "end_at_sigma": 0,
      "spacing": "cosine",
      "sigmas": [
        "124",
        0
      ]
    },
    "class_type": "H3SigmaRefiner",
    "_meta": {
      "title": "H3 Sigma Refiner"
    }
  },
  "256": {
    "inputs": {
      "image": "07d2e1d22673808899bba100354351b0d4b5b723a10358c7a9ffe92ec0c98ddc.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "257": {
    "inputs": {
      "image": "56a596334282d0057a0847e7a1f2714e8aa27725718b5a162e3ac33c02e42b17.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "258": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "259": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "260": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "263": {
    "inputs": {
      "model_name": "minimax_h3_latent_upscaler_3d_fp16.safetensors",
      "mode": "scale by multiplier",
      "mode.scale": 2,
      "align": 32,
      "device": "cuda",
      "precision": "fp16",
      "enable_chunking": True,
      "latent": [
        "211",
        0
      ]
    },
    "class_type": "MinimaxH3LatentUpscaler3D",
    "_meta": {
      "title": "Minimax H3 Latent Upscaler (3D)"
    }
  },
  "271": {
    "inputs": {
      "frame_rate": 24,
      "loop_count": 0,
      "filename_prefix": "第二次采样",
      "format": "video/h264-mp4",
      "pix_fmt": "yuv420p",
      "crf": 19,
      "save_metadata": True,
      "trim_to_audio": False,
      "pingpong": False,
      "save_output": True,
      "no_preview": False,
      "images": [
        "219",
        0
      ],
      "audio": [
        "218",
        0
      ]
    },
    "class_type": "VHS_VideoCombine",
    "_meta": {
      "title": "Video Combine 🎥🅥🅗🅢"
    }
  },
  "272": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "273": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "274": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "275": {
    "inputs": {
      "audio": "0ea9bca3948a0baf7983804066a8884203e6452b1c37a109bf6e5dc24e616996.flac",
      "audioUI": ""
    },
    "class_type": "LoadAudio",
    "_meta": {
      "title": "Load Audio"
    }
  }
}

# minimax_h3 5张图片加上1个参考音频
minimax_h3_5_image_1_audio_json = {
  "115": {
    "inputs": {
      "aspect_ratio": "16:9 (Widescreen)",
      "megapixels": 0.5,
      "multiple": 32
    },
    "class_type": "ResolutionSelector",
    "_meta": {
      "title": "PASS1 / 16:9 / 0.5MP"
    }
  },
  "119": {
    "inputs": {
      "vae_name": "minimax_h3_video_vae_fp16.safetensors"
    },
    "class_type": "VAELoader",
    "_meta": {
      "title": "Load VAE"
    }
  },
  "120": {
    "inputs": {
      "vae_name": "minimax_h3_audio_vae_fp32.safetensors"
    },
    "class_type": "VAELoader",
    "_meta": {
      "title": "Load VAE"
    }
  },
  "123": {
    "inputs": {
      "sampler_name": "euler"
    },
    "class_type": "KSamplerSelect",
    "_meta": {
      "title": "KSamplerSelect"
    }
  },
  "124": {
    "inputs": {
      "scheduler": "simple",
      "steps": 10,
      "denoise": 1,
      "model": [
        "141",
        0
      ]
    },
    "class_type": "BasicScheduler",
    "_meta": {
      "title": "BasicScheduler"
    }
  },
  "125": {
    "inputs": {
      "noise": [
        "129",
        0
      ],
      "guider": [
        "126",
        0
      ],
      "sampler": [
        "123",
        0
      ],
      "sigmas": [
        "208",
        0
      ],
      "latent_image": [
        "136",
        1
      ]
    },
    "class_type": "SamplerCustomAdvanced",
    "_meta": {
      "title": "SamplerCustomAdvanced"
    }
  },
  "126": {
    "inputs": {
      "model": [
        "141",
        0
      ],
      "conditioning": [
        "136",
        0
      ]
    },
    "class_type": "BasicGuider",
    "_meta": {
      "title": "Basic Guider"
    }
  },
  "127": {
    "inputs": {
      "unet_name": "minimax_h3_hybrid_fl2va_ref2va_b25-49-int8.safetensors",
      "weight_dtype": "default"
    },
    "class_type": "UNETLoader",
    "_meta": {
      "title": "Load Diffusion Model"
    }
  },
  "128": {
    "inputs": {
      "clip_name": "qwen3vl_32b_minimax_h3_int8_convrot.safetensors",
      "type": "minimax",
      "device": "default"
    },
    "class_type": "CLIPLoader",
    "_meta": {
      "title": "Load CLIP"
    }
  },
  "129": {
    "inputs": {
      "noise_seed": 999
    },
    "class_type": "RandomNoise",
    "_meta": {
      "title": "RandomNoise"
    }
  },
  "131": {
    "inputs": {
      "expression": "max(5, round(a * 24)) + (5 - (max(5, round(a * 24)) % 17)) % 17",
      "values.a": [
        "132",
        0
      ]
    },
    "class_type": "ComfyMathExpression",
    "_meta": {
      "title": "Math Expression"
    }
  },
  "132": {
    "inputs": {
      "value": 6
    },
    "class_type": "PrimitiveFloat",
    "_meta": {
      "title": "Float (Duration)"
    }
  },
  "136": {
    "inputs": {
      "prompt": [
        "138",
        0
      ],
      "width": [
        "115",
        0
      ],
      "height": [
        "115",
        1
      ],
      "length": [
        "131",
        1
      ],
      "task_type": "auto",
      "audio_mode": "native",
      "audio_denoise_strength": 1,
      "add_source_as_reference": False,
      "prompt_primary_audio_ordinal": 0,
      "strict_prompt_tags": True,
      "ref_image_size": "match",
      "reference_video_policy": "official_2_to_15s",
      "allow_above_reference_area": True,
      "clip": [
        "128",
        0
      ],
      "video_vae": [
        "119",
        0
      ],
      "audio_vae": [
        "120",
        0
      ],
      "ref_images.ref_image_0": [
        "139",
        0
      ],
      "ref_images.ref_image_1": [
        "256",
        0
      ],
      "ref_images.ref_image_2": [
        "257",
        0
      ],
      "ref_images.ref_image_3": [
        "258",
        0
      ],
      "ref_images.ref_image_4": [
        "259",
        0
      ],
      "ref_audios.ref_audio_0": [
        "275",
        0
      ]
    },
    "class_type": "MiniMaxH3AudioConditioningT8",
    "_meta": {
      "title": "T8 条件节点｜通用模式"
    }
  },
  "138": {
    "inputs": {
      "value": "subject_definitions:\\n<Subject 1> is Lin Che from <Picture 1>, a 29-year-old Chinese woman with a chin-length black bob, a small mole at the outer end of her left eyebrow, a dark red buttoned knitted cardigan over a white crew-neck top and black trousers. Preserve her facial identity, natural skin and wardrobe; the three standing views do not dictate her seated performance.\\n<Subject 2> is Chen Li from <Picture 2>, a 48-year-old Chinese man with a square face, short black hair graying at the temples, a slight gap in his right eyebrow, a medium-gray knitted cardigan over a pale blue shirt and dark gray trousers. Preserve his face, age, hair and clothing, not the reference pose.\\n<Subject 3> is the same empty meeting room from <Picture 3>: a matte light-gray rectangular table with its long axis east-west, one chair at each east and west short end, a closed high frosted window in the north wall, a low dark-green six-cubby cabinet against the west wall and a closed brown door in the south wall. Preserve the world-space layout and matte surfaces. Omit the four-view borders, reference viewpoints and incidental objects; the room contains only the two directed people and the one directed recorder.\\n\\nsummary:\\n[reference generation] A 6-second continuous live-action medium shot in <Subject 3>. Lin Che establishes that the recorder is already running and challenges Chen Li to speak on record. The three pictures supply identity and room design, with newly directed framing rather than exact endpoints.\\n\\nretention_analysis:\\n<Subject 1> (appears in [Shot 1]): fully_preserved - Keep Lin Che's identity, bob, dark red cardigan and white inner top while directing the specified seated performance.\\n<Subject 2> (appears in [Shot 1]): fully_preserved - Keep Chen Li's identity, gray temples, gray cardigan and pale blue shirt; the directed seated pose replaces the standing reference.\\n<Subject 3> (appears in [Shot 1]): partially_preserved - Keep the fixed room topology, north-window light, west cabinet and table material; omit multi-view panels and reference framing. The initial camera composition is newly directed.\\n\\ndetailed_description:\\nThe target video is a restrained contemporary Chinese live-action suspense drama, with natural skin texture, readable faces and softly lit matte surfaces.\\n[Shot 1] The camera occupies the open southeast aisle at approximately (1.5,-1.5,1.3) meters relative to the table center and faces northwest toward <Subject 1>. She is seated at the west end on screen-left, torso and head turned east toward <Subject 2>, with her gaze going screen-right. Her chin-length bob, natural eyebrow mark and dark red cardigan remain visible. His gray-clad shoulder and pale blue collar occupy only the extreme right foreground; his body remains at the east seat, and his shoulder does not obscure her face, hands or the recorder. The background shows the west green cabinet and only a geometrically plausible part of the north wall and window. The south door stays behind the camera and out of frame.\\nBoth remain seated on the same two chairs, feet on the floor, with neither changing seats or turning away. <Subject 1>'s two empty hands rest separately on the west table edge; <Subject 2>'s left hand rests on the east edge. There is exactly one small black rectangular audio recorder, about 10 by 3 by 1 centimeters, lying flat on the matte tabletop, long axis east-west and its single red indicator steadily lit. It has no readable display. Its center is 0.35 meters east and 0.12 meters south of the table center. His right fingertips rest on the tabletop three centimeters east of the recorder, separated from its casing. The recorder and both hands remain still until any explicitly directed action.\\nHold the initial pose for about one second. <Subject 1> (S1), using a clear low young-adult female Mandarin voice, measured and direct, says <d>[Chinese] 录音开着。你还要我关掉？</d> The statement about recording is a condition of this conversation, not a command to press a button. Finish speaking by about 4.5 seconds, close the mouth and hold eye contact for the remaining beat. Only speech-related lips, small facial tension and natural breathing change. The listener keeps a closed mouth and still hands. No control is pressed, and the indicator remains steadily red.\\nThe sole key is diffused cool-neutral daylight from the fixed high north window, above seated eye level. It softly illuminates the north-facing cheek, the upper knuckles and the recorder's top plane. Weak, slightly warm bounce from the south wall preserves detail on the shadow side without creating another hard shadow. Hair casts a gentle edge at the jaw, and sleeves retain soft folds. Small contact shadows attach hands and the recorder to the tabletop and extend toward the south in world space; the stationary recorder retains a stationary contact shadow. Keep source positions, exposure and white balance steady. Matte surfaces produce subdued highlights rather than flashes. Changing the viewpoint must not relocate the light to the camera side.\\nUse a 40 mm-equivalent lens at seated eye height, in a medium composition with enough depth of field for the featured face, hands and recorder to remain legible. Focus stays on the featured person's eyes without a focus pull. The camera remains fixed throughout; position, orientation, focal length and framing stay unchanged. The foreground shoulder remains a narrow edge element, not a moving wipe or obstruction. Keep the same single shot from beginning to end.\\nThe output is one full-frame scene, with no reference panels, additional people, automatic captions or decorative overlays. Preserve the settled end pose for the adjacent reverse-angle cut.\\n\\noverall_soundscape:\\nLow steady ventilation and distant, muffled room ambience, with subtle breaths and fabric noise. The stationary recorder produces no playback, beeps or repeated scrape. Keep the room tone unobtrusive beneath the voice.\\n\\nnon_diegetic_music:\\nN/A"
    },
    "class_type": "PrimitiveStringMultiline",
    "_meta": {
      "title": "Input Text (Prompt)"
    }
  },
  "139": {
    "inputs": {
      "image": "2636c786c4c0e6c33db28ba14bbe1c381ed4f7cbd8ae925b745e370640e55fea.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "141": {
    "inputs": {
      "max_resolution": 1024,
      "jpeg_quality": 80,
      "suppress_default_preview": True,
      "preview_frames": [
        "131",
        1
      ],
      "preview_fps": 12,
      "tiny_vae": "taeh3.safetensors",
      "model": [
        "178",
        0
      ]
    },
    "class_type": "ModelPreviewOverrideKJ",
    "_meta": {
      "title": "Model Preview Override KJ"
    }
  },
  "147": {
    "inputs": {
      "lora_name": "minimax_h3_ref2v_turbo_8step_v1.0_768p_comfyui_bf16.safetensors",
      "strength_model": 1.0000000000000002,
      "model": [
        "127",
        0
      ]
    },
    "class_type": "LoraLoaderModelOnly",
    "_meta": {
      "title": "Load LoRA"
    }
  },
  "149": {
    "inputs": {
      "shift_video": 12,
      "shift_audio": 3,
      "model": [
        "147",
        0
      ]
    },
    "class_type": "MiniMaxH3SigmaShift",
    "_meta": {
      "title": "ModelSamplingMiniMaxH3"
    }
  },
  "178": {
    "inputs": {
      "attention": "comfy kitchen attention",
      "model": [
        "149",
        0
      ]
    },
    "class_type": "ModelAttentionBackend",
    "_meta": {
      "title": "ModelAttentionBackend"
    }
  },
  "208": {
    "inputs": {
      "step": 6,
      "sigmas": [
        "254",
        0
      ]
    },
    "class_type": "SplitSigmas",
    "_meta": {
      "title": "SplitSigmas"
    }
  },
  "209": {
    "inputs": {
      "noise": [
        "129",
        0
      ],
      "guider": [
        "126",
        0
      ],
      "sampler": [
        "123",
        0
      ],
      "sigmas": [
        "208",
        1
      ],
      "latent_image": [
        "212",
        0
      ]
    },
    "class_type": "SamplerCustomAdvanced",
    "_meta": {
      "title": "SamplerCustomAdvanced"
    }
  },
  "211": {
    "inputs": {
      "av_latent": [
        "125",
        1
      ]
    },
    "class_type": "LTXVSeparateAVLatent",
    "_meta": {
      "title": "Separate AV Latent"
    }
  },
  "212": {
    "inputs": {
      "video_latent": [
        "263",
        0
      ],
      "audio_latent": [
        "211",
        1
      ]
    },
    "class_type": "LTXVConcatAVLatent",
    "_meta": {
      "title": "Concat AV Latent"
    }
  },
  "218": {
    "inputs": {
      "samples": [
        "209",
        0
      ],
      "vae": [
        "120",
        0
      ]
    },
    "class_type": "VAEDecodeAudio",
    "_meta": {
      "title": "VAE Decode Audio"
    }
  },
  "219": {
    "inputs": {
      "samples": [
        "209",
        0
      ],
      "vae": [
        "119",
        0
      ]
    },
    "class_type": "VAEDecode",
    "_meta": {
      "title": "VAE Decode"
    }
  },
  "254": {
    "inputs": {
      "extra_steps": 1,
      "start_at_sigma": 0.7,
      "end_at_sigma": 0,
      "spacing": "cosine",
      "sigmas": [
        "124",
        0
      ]
    },
    "class_type": "H3SigmaRefiner",
    "_meta": {
      "title": "H3 Sigma Refiner"
    }
  },
  "256": {
    "inputs": {
      "image": "07d2e1d22673808899bba100354351b0d4b5b723a10358c7a9ffe92ec0c98ddc.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "257": {
    "inputs": {
      "image": "56a596334282d0057a0847e7a1f2714e8aa27725718b5a162e3ac33c02e42b17.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "258": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "259": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "260": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "263": {
    "inputs": {
      "model_name": "minimax_h3_latent_upscaler_3d_fp16.safetensors",
      "mode": "scale by multiplier",
      "mode.scale": 2,
      "align": 32,
      "device": "cuda",
      "precision": "fp16",
      "enable_chunking": True,
      "latent": [
        "211",
        0
      ]
    },
    "class_type": "MinimaxH3LatentUpscaler3D",
    "_meta": {
      "title": "Minimax H3 Latent Upscaler (3D)"
    }
  },
  "271": {
    "inputs": {
      "frame_rate": 24,
      "loop_count": 0,
      "filename_prefix": "第二次采样",
      "format": "video/h264-mp4",
      "pix_fmt": "yuv420p",
      "crf": 19,
      "save_metadata": True,
      "trim_to_audio": False,
      "pingpong": False,
      "save_output": True,
      "no_preview": False,
      "images": [
        "219",
        0
      ],
      "audio": [
        "218",
        0
      ]
    },
    "class_type": "VHS_VideoCombine",
    "_meta": {
      "title": "Video Combine 🎥🅥🅗🅢"
    }
  },
  "272": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "273": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "274": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "275": {
    "inputs": {
      "audio": "0ea9bca3948a0baf7983804066a8884203e6452b1c37a109bf6e5dc24e616996.flac",
      "audioUI": ""
    },
    "class_type": "LoadAudio",
    "_meta": {
      "title": "Load Audio"
    }
  }
}

# minimax_h3 4张图片加上1个参考音频
minimax_h3_4_image_1_audio_json = {
  "115": {
    "inputs": {
      "aspect_ratio": "16:9 (Widescreen)",
      "megapixels": 0.5,
      "multiple": 32
    },
    "class_type": "ResolutionSelector",
    "_meta": {
      "title": "PASS1 / 16:9 / 0.5MP"
    }
  },
  "119": {
    "inputs": {
      "vae_name": "minimax_h3_video_vae_fp16.safetensors"
    },
    "class_type": "VAELoader",
    "_meta": {
      "title": "Load VAE"
    }
  },
  "120": {
    "inputs": {
      "vae_name": "minimax_h3_audio_vae_fp32.safetensors"
    },
    "class_type": "VAELoader",
    "_meta": {
      "title": "Load VAE"
    }
  },
  "123": {
    "inputs": {
      "sampler_name": "euler"
    },
    "class_type": "KSamplerSelect",
    "_meta": {
      "title": "KSamplerSelect"
    }
  },
  "124": {
    "inputs": {
      "scheduler": "simple",
      "steps": 10,
      "denoise": 1,
      "model": [
        "141",
        0
      ]
    },
    "class_type": "BasicScheduler",
    "_meta": {
      "title": "BasicScheduler"
    }
  },
  "125": {
    "inputs": {
      "noise": [
        "129",
        0
      ],
      "guider": [
        "126",
        0
      ],
      "sampler": [
        "123",
        0
      ],
      "sigmas": [
        "208",
        0
      ],
      "latent_image": [
        "136",
        1
      ]
    },
    "class_type": "SamplerCustomAdvanced",
    "_meta": {
      "title": "SamplerCustomAdvanced"
    }
  },
  "126": {
    "inputs": {
      "model": [
        "141",
        0
      ],
      "conditioning": [
        "136",
        0
      ]
    },
    "class_type": "BasicGuider",
    "_meta": {
      "title": "Basic Guider"
    }
  },
  "127": {
    "inputs": {
      "unet_name": "minimax_h3_hybrid_fl2va_ref2va_b25-49-int8.safetensors",
      "weight_dtype": "default"
    },
    "class_type": "UNETLoader",
    "_meta": {
      "title": "Load Diffusion Model"
    }
  },
  "128": {
    "inputs": {
      "clip_name": "qwen3vl_32b_minimax_h3_int8_convrot.safetensors",
      "type": "minimax",
      "device": "default"
    },
    "class_type": "CLIPLoader",
    "_meta": {
      "title": "Load CLIP"
    }
  },
  "129": {
    "inputs": {
      "noise_seed": 999
    },
    "class_type": "RandomNoise",
    "_meta": {
      "title": "RandomNoise"
    }
  },
  "131": {
    "inputs": {
      "expression": "max(5, round(a * 24)) + (5 - (max(5, round(a * 24)) % 17)) % 17",
      "values.a": [
        "132",
        0
      ]
    },
    "class_type": "ComfyMathExpression",
    "_meta": {
      "title": "Math Expression"
    }
  },
  "132": {
    "inputs": {
      "value": 6
    },
    "class_type": "PrimitiveFloat",
    "_meta": {
      "title": "Float (Duration)"
    }
  },
  "136": {
    "inputs": {
      "prompt": [
        "138",
        0
      ],
      "width": [
        "115",
        0
      ],
      "height": [
        "115",
        1
      ],
      "length": [
        "131",
        1
      ],
      "task_type": "auto",
      "audio_mode": "native",
      "audio_denoise_strength": 1,
      "add_source_as_reference": False,
      "prompt_primary_audio_ordinal": 0,
      "strict_prompt_tags": True,
      "ref_image_size": "match",
      "reference_video_policy": "official_2_to_15s",
      "allow_above_reference_area": True,
      "clip": [
        "128",
        0
      ],
      "video_vae": [
        "119",
        0
      ],
      "audio_vae": [
        "120",
        0
      ],
      "ref_images.ref_image_0": [
        "139",
        0
      ],
      "ref_images.ref_image_1": [
        "256",
        0
      ],
      "ref_images.ref_image_2": [
        "257",
        0
      ],
      "ref_images.ref_image_3": [
        "258",
        0
      ],
      "ref_audios.ref_audio_0": [
        "275",
        0
      ]
    },
    "class_type": "MiniMaxH3AudioConditioningT8",
    "_meta": {
      "title": "T8 条件节点｜通用模式"
    }
  },
  "138": {
    "inputs": {
      "value": "subject_definitions:\\n<Subject 1> is Lin Che from <Picture 1>, a 29-year-old Chinese woman with a chin-length black bob, a small mole at the outer end of her left eyebrow, a dark red buttoned knitted cardigan over a white crew-neck top and black trousers. Preserve her facial identity, natural skin and wardrobe; the three standing views do not dictate her seated performance.\\n<Subject 2> is Chen Li from <Picture 2>, a 48-year-old Chinese man with a square face, short black hair graying at the temples, a slight gap in his right eyebrow, a medium-gray knitted cardigan over a pale blue shirt and dark gray trousers. Preserve his face, age, hair and clothing, not the reference pose.\\n<Subject 3> is the same empty meeting room from <Picture 3>: a matte light-gray rectangular table with its long axis east-west, one chair at each east and west short end, a closed high frosted window in the north wall, a low dark-green six-cubby cabinet against the west wall and a closed brown door in the south wall. Preserve the world-space layout and matte surfaces. Omit the four-view borders, reference viewpoints and incidental objects; the room contains only the two directed people and the one directed recorder.\\n\\nsummary:\\n[reference generation] A 6-second continuous live-action medium shot in <Subject 3>. Lin Che establishes that the recorder is already running and challenges Chen Li to speak on record. The three pictures supply identity and room design, with newly directed framing rather than exact endpoints.\\n\\nretention_analysis:\\n<Subject 1> (appears in [Shot 1]): fully_preserved - Keep Lin Che's identity, bob, dark red cardigan and white inner top while directing the specified seated performance.\\n<Subject 2> (appears in [Shot 1]): fully_preserved - Keep Chen Li's identity, gray temples, gray cardigan and pale blue shirt; the directed seated pose replaces the standing reference.\\n<Subject 3> (appears in [Shot 1]): partially_preserved - Keep the fixed room topology, north-window light, west cabinet and table material; omit multi-view panels and reference framing. The initial camera composition is newly directed.\\n\\ndetailed_description:\\nThe target video is a restrained contemporary Chinese live-action suspense drama, with natural skin texture, readable faces and softly lit matte surfaces.\\n[Shot 1] The camera occupies the open southeast aisle at approximately (1.5,-1.5,1.3) meters relative to the table center and faces northwest toward <Subject 1>. She is seated at the west end on screen-left, torso and head turned east toward <Subject 2>, with her gaze going screen-right. Her chin-length bob, natural eyebrow mark and dark red cardigan remain visible. His gray-clad shoulder and pale blue collar occupy only the extreme right foreground; his body remains at the east seat, and his shoulder does not obscure her face, hands or the recorder. The background shows the west green cabinet and only a geometrically plausible part of the north wall and window. The south door stays behind the camera and out of frame.\\nBoth remain seated on the same two chairs, feet on the floor, with neither changing seats or turning away. <Subject 1>'s two empty hands rest separately on the west table edge; <Subject 2>'s left hand rests on the east edge. There is exactly one small black rectangular audio recorder, about 10 by 3 by 1 centimeters, lying flat on the matte tabletop, long axis east-west and its single red indicator steadily lit. It has no readable display. Its center is 0.35 meters east and 0.12 meters south of the table center. His right fingertips rest on the tabletop three centimeters east of the recorder, separated from its casing. The recorder and both hands remain still until any explicitly directed action.\\nHold the initial pose for about one second. <Subject 1> (S1), using a clear low young-adult female Mandarin voice, measured and direct, says <d>[Chinese] 录音开着。你还要我关掉？</d> The statement about recording is a condition of this conversation, not a command to press a button. Finish speaking by about 4.5 seconds, close the mouth and hold eye contact for the remaining beat. Only speech-related lips, small facial tension and natural breathing change. The listener keeps a closed mouth and still hands. No control is pressed, and the indicator remains steadily red.\\nThe sole key is diffused cool-neutral daylight from the fixed high north window, above seated eye level. It softly illuminates the north-facing cheek, the upper knuckles and the recorder's top plane. Weak, slightly warm bounce from the south wall preserves detail on the shadow side without creating another hard shadow. Hair casts a gentle edge at the jaw, and sleeves retain soft folds. Small contact shadows attach hands and the recorder to the tabletop and extend toward the south in world space; the stationary recorder retains a stationary contact shadow. Keep source positions, exposure and white balance steady. Matte surfaces produce subdued highlights rather than flashes. Changing the viewpoint must not relocate the light to the camera side.\\nUse a 40 mm-equivalent lens at seated eye height, in a medium composition with enough depth of field for the featured face, hands and recorder to remain legible. Focus stays on the featured person's eyes without a focus pull. The camera remains fixed throughout; position, orientation, focal length and framing stay unchanged. The foreground shoulder remains a narrow edge element, not a moving wipe or obstruction. Keep the same single shot from beginning to end.\\nThe output is one full-frame scene, with no reference panels, additional people, automatic captions or decorative overlays. Preserve the settled end pose for the adjacent reverse-angle cut.\\n\\noverall_soundscape:\\nLow steady ventilation and distant, muffled room ambience, with subtle breaths and fabric noise. The stationary recorder produces no playback, beeps or repeated scrape. Keep the room tone unobtrusive beneath the voice.\\n\\nnon_diegetic_music:\\nN/A"
    },
    "class_type": "PrimitiveStringMultiline",
    "_meta": {
      "title": "Input Text (Prompt)"
    }
  },
  "139": {
    "inputs": {
      "image": "2636c786c4c0e6c33db28ba14bbe1c381ed4f7cbd8ae925b745e370640e55fea.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "141": {
    "inputs": {
      "max_resolution": 1024,
      "jpeg_quality": 80,
      "suppress_default_preview": True,
      "preview_frames": [
        "131",
        1
      ],
      "preview_fps": 12,
      "tiny_vae": "taeh3.safetensors",
      "model": [
        "178",
        0
      ]
    },
    "class_type": "ModelPreviewOverrideKJ",
    "_meta": {
      "title": "Model Preview Override KJ"
    }
  },
  "147": {
    "inputs": {
      "lora_name": "minimax_h3_ref2v_turbo_8step_v1.0_768p_comfyui_bf16.safetensors",
      "strength_model": 1.0000000000000002,
      "model": [
        "127",
        0
      ]
    },
    "class_type": "LoraLoaderModelOnly",
    "_meta": {
      "title": "Load LoRA"
    }
  },
  "149": {
    "inputs": {
      "shift_video": 12,
      "shift_audio": 3,
      "model": [
        "147",
        0
      ]
    },
    "class_type": "MiniMaxH3SigmaShift",
    "_meta": {
      "title": "ModelSamplingMiniMaxH3"
    }
  },
  "178": {
    "inputs": {
      "attention": "comfy kitchen attention",
      "model": [
        "149",
        0
      ]
    },
    "class_type": "ModelAttentionBackend",
    "_meta": {
      "title": "ModelAttentionBackend"
    }
  },
  "208": {
    "inputs": {
      "step": 6,
      "sigmas": [
        "254",
        0
      ]
    },
    "class_type": "SplitSigmas",
    "_meta": {
      "title": "SplitSigmas"
    }
  },
  "209": {
    "inputs": {
      "noise": [
        "129",
        0
      ],
      "guider": [
        "126",
        0
      ],
      "sampler": [
        "123",
        0
      ],
      "sigmas": [
        "208",
        1
      ],
      "latent_image": [
        "212",
        0
      ]
    },
    "class_type": "SamplerCustomAdvanced",
    "_meta": {
      "title": "SamplerCustomAdvanced"
    }
  },
  "211": {
    "inputs": {
      "av_latent": [
        "125",
        1
      ]
    },
    "class_type": "LTXVSeparateAVLatent",
    "_meta": {
      "title": "Separate AV Latent"
    }
  },
  "212": {
    "inputs": {
      "video_latent": [
        "263",
        0
      ],
      "audio_latent": [
        "211",
        1
      ]
    },
    "class_type": "LTXVConcatAVLatent",
    "_meta": {
      "title": "Concat AV Latent"
    }
  },
  "218": {
    "inputs": {
      "samples": [
        "209",
        0
      ],
      "vae": [
        "120",
        0
      ]
    },
    "class_type": "VAEDecodeAudio",
    "_meta": {
      "title": "VAE Decode Audio"
    }
  },
  "219": {
    "inputs": {
      "samples": [
        "209",
        0
      ],
      "vae": [
        "119",
        0
      ]
    },
    "class_type": "VAEDecode",
    "_meta": {
      "title": "VAE Decode"
    }
  },
  "254": {
    "inputs": {
      "extra_steps": 1,
      "start_at_sigma": 0.7,
      "end_at_sigma": 0,
      "spacing": "cosine",
      "sigmas": [
        "124",
        0
      ]
    },
    "class_type": "H3SigmaRefiner",
    "_meta": {
      "title": "H3 Sigma Refiner"
    }
  },
  "256": {
    "inputs": {
      "image": "07d2e1d22673808899bba100354351b0d4b5b723a10358c7a9ffe92ec0c98ddc.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "257": {
    "inputs": {
      "image": "56a596334282d0057a0847e7a1f2714e8aa27725718b5a162e3ac33c02e42b17.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "258": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "259": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "260": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "263": {
    "inputs": {
      "model_name": "minimax_h3_latent_upscaler_3d_fp16.safetensors",
      "mode": "scale by multiplier",
      "mode.scale": 2,
      "align": 32,
      "device": "cuda",
      "precision": "fp16",
      "enable_chunking": True,
      "latent": [
        "211",
        0
      ]
    },
    "class_type": "MinimaxH3LatentUpscaler3D",
    "_meta": {
      "title": "Minimax H3 Latent Upscaler (3D)"
    }
  },
  "271": {
    "inputs": {
      "frame_rate": 24,
      "loop_count": 0,
      "filename_prefix": "第二次采样",
      "format": "video/h264-mp4",
      "pix_fmt": "yuv420p",
      "crf": 19,
      "save_metadata": True,
      "trim_to_audio": False,
      "pingpong": False,
      "save_output": True,
      "no_preview": False,
      "images": [
        "219",
        0
      ],
      "audio": [
        "218",
        0
      ]
    },
    "class_type": "VHS_VideoCombine",
    "_meta": {
      "title": "Video Combine 🎥🅥🅗🅢"
    }
  },
  "272": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "273": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "274": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "275": {
    "inputs": {
      "audio": "0ea9bca3948a0baf7983804066a8884203e6452b1c37a109bf6e5dc24e616996.flac",
      "audioUI": ""
    },
    "class_type": "LoadAudio",
    "_meta": {
      "title": "Load Audio"
    }
  }
}

# minimax_h3 3张图片加上1个参考音频
minimax_h3_3_image_1_audio_json = {
  "115": {
    "inputs": {
      "aspect_ratio": "16:9 (Widescreen)",
      "megapixels": 0.5,
      "multiple": 32
    },
    "class_type": "ResolutionSelector",
    "_meta": {
      "title": "PASS1 / 16:9 / 0.5MP"
    }
  },
  "119": {
    "inputs": {
      "vae_name": "minimax_h3_video_vae_fp16.safetensors"
    },
    "class_type": "VAELoader",
    "_meta": {
      "title": "Load VAE"
    }
  },
  "120": {
    "inputs": {
      "vae_name": "minimax_h3_audio_vae_fp32.safetensors"
    },
    "class_type": "VAELoader",
    "_meta": {
      "title": "Load VAE"
    }
  },
  "123": {
    "inputs": {
      "sampler_name": "euler"
    },
    "class_type": "KSamplerSelect",
    "_meta": {
      "title": "KSamplerSelect"
    }
  },
  "124": {
    "inputs": {
      "scheduler": "simple",
      "steps": 10,
      "denoise": 1,
      "model": [
        "141",
        0
      ]
    },
    "class_type": "BasicScheduler",
    "_meta": {
      "title": "BasicScheduler"
    }
  },
  "125": {
    "inputs": {
      "noise": [
        "129",
        0
      ],
      "guider": [
        "126",
        0
      ],
      "sampler": [
        "123",
        0
      ],
      "sigmas": [
        "208",
        0
      ],
      "latent_image": [
        "136",
        1
      ]
    },
    "class_type": "SamplerCustomAdvanced",
    "_meta": {
      "title": "SamplerCustomAdvanced"
    }
  },
  "126": {
    "inputs": {
      "model": [
        "141",
        0
      ],
      "conditioning": [
        "136",
        0
      ]
    },
    "class_type": "BasicGuider",
    "_meta": {
      "title": "Basic Guider"
    }
  },
  "127": {
    "inputs": {
      "unet_name": "minimax_h3_hybrid_fl2va_ref2va_b25-49-int8.safetensors",
      "weight_dtype": "default"
    },
    "class_type": "UNETLoader",
    "_meta": {
      "title": "Load Diffusion Model"
    }
  },
  "128": {
    "inputs": {
      "clip_name": "qwen3vl_32b_minimax_h3_int8_convrot.safetensors",
      "type": "minimax",
      "device": "default"
    },
    "class_type": "CLIPLoader",
    "_meta": {
      "title": "Load CLIP"
    }
  },
  "129": {
    "inputs": {
      "noise_seed": 999
    },
    "class_type": "RandomNoise",
    "_meta": {
      "title": "RandomNoise"
    }
  },
  "131": {
    "inputs": {
      "expression": "max(5, round(a * 24)) + (5 - (max(5, round(a * 24)) % 17)) % 17",
      "values.a": [
        "132",
        0
      ]
    },
    "class_type": "ComfyMathExpression",
    "_meta": {
      "title": "Math Expression"
    }
  },
  "132": {
    "inputs": {
      "value": 6
    },
    "class_type": "PrimitiveFloat",
    "_meta": {
      "title": "Float (Duration)"
    }
  },
  "136": {
    "inputs": {
      "prompt": [
        "138",
        0
      ],
      "width": [
        "115",
        0
      ],
      "height": [
        "115",
        1
      ],
      "length": [
        "131",
        1
      ],
      "task_type": "auto",
      "audio_mode": "native",
      "audio_denoise_strength": 1,
      "add_source_as_reference": False,
      "prompt_primary_audio_ordinal": 0,
      "strict_prompt_tags": True,
      "ref_image_size": "match",
      "reference_video_policy": "official_2_to_15s",
      "allow_above_reference_area": True,
      "clip": [
        "128",
        0
      ],
      "video_vae": [
        "119",
        0
      ],
      "audio_vae": [
        "120",
        0
      ],
      "ref_images.ref_image_0": [
        "139",
        0
      ],
      "ref_images.ref_image_1": [
        "256",
        0
      ],
      "ref_images.ref_image_2": [
        "257",
        0
      ],
      "ref_audios.ref_audio_0": [
        "275",
        0
      ]
    },
    "class_type": "MiniMaxH3AudioConditioningT8",
    "_meta": {
      "title": "T8 条件节点｜通用模式"
    }
  },
  "138": {
    "inputs": {
      "value": "subject_definitions:\\n<Subject 1> is Lin Che from <Picture 1>, a 29-year-old Chinese woman with a chin-length black bob, a small mole at the outer end of her left eyebrow, a dark red buttoned knitted cardigan over a white crew-neck top and black trousers. Preserve her facial identity, natural skin and wardrobe; the three standing views do not dictate her seated performance.\\n<Subject 2> is Chen Li from <Picture 2>, a 48-year-old Chinese man with a square face, short black hair graying at the temples, a slight gap in his right eyebrow, a medium-gray knitted cardigan over a pale blue shirt and dark gray trousers. Preserve his face, age, hair and clothing, not the reference pose.\\n<Subject 3> is the same empty meeting room from <Picture 3>: a matte light-gray rectangular table with its long axis east-west, one chair at each east and west short end, a closed high frosted window in the north wall, a low dark-green six-cubby cabinet against the west wall and a closed brown door in the south wall. Preserve the world-space layout and matte surfaces. Omit the four-view borders, reference viewpoints and incidental objects; the room contains only the two directed people and the one directed recorder.\\n\\nsummary:\\n[reference generation] A 6-second continuous live-action medium shot in <Subject 3>. Lin Che establishes that the recorder is already running and challenges Chen Li to speak on record. The three pictures supply identity and room design, with newly directed framing rather than exact endpoints.\\n\\nretention_analysis:\\n<Subject 1> (appears in [Shot 1]): fully_preserved - Keep Lin Che's identity, bob, dark red cardigan and white inner top while directing the specified seated performance.\\n<Subject 2> (appears in [Shot 1]): fully_preserved - Keep Chen Li's identity, gray temples, gray cardigan and pale blue shirt; the directed seated pose replaces the standing reference.\\n<Subject 3> (appears in [Shot 1]): partially_preserved - Keep the fixed room topology, north-window light, west cabinet and table material; omit multi-view panels and reference framing. The initial camera composition is newly directed.\\n\\ndetailed_description:\\nThe target video is a restrained contemporary Chinese live-action suspense drama, with natural skin texture, readable faces and softly lit matte surfaces.\\n[Shot 1] The camera occupies the open southeast aisle at approximately (1.5,-1.5,1.3) meters relative to the table center and faces northwest toward <Subject 1>. She is seated at the west end on screen-left, torso and head turned east toward <Subject 2>, with her gaze going screen-right. Her chin-length bob, natural eyebrow mark and dark red cardigan remain visible. His gray-clad shoulder and pale blue collar occupy only the extreme right foreground; his body remains at the east seat, and his shoulder does not obscure her face, hands or the recorder. The background shows the west green cabinet and only a geometrically plausible part of the north wall and window. The south door stays behind the camera and out of frame.\\nBoth remain seated on the same two chairs, feet on the floor, with neither changing seats or turning away. <Subject 1>'s two empty hands rest separately on the west table edge; <Subject 2>'s left hand rests on the east edge. There is exactly one small black rectangular audio recorder, about 10 by 3 by 1 centimeters, lying flat on the matte tabletop, long axis east-west and its single red indicator steadily lit. It has no readable display. Its center is 0.35 meters east and 0.12 meters south of the table center. His right fingertips rest on the tabletop three centimeters east of the recorder, separated from its casing. The recorder and both hands remain still until any explicitly directed action.\\nHold the initial pose for about one second. <Subject 1> (S1), using a clear low young-adult female Mandarin voice, measured and direct, says <d>[Chinese] 录音开着。你还要我关掉？</d> The statement about recording is a condition of this conversation, not a command to press a button. Finish speaking by about 4.5 seconds, close the mouth and hold eye contact for the remaining beat. Only speech-related lips, small facial tension and natural breathing change. The listener keeps a closed mouth and still hands. No control is pressed, and the indicator remains steadily red.\\nThe sole key is diffused cool-neutral daylight from the fixed high north window, above seated eye level. It softly illuminates the north-facing cheek, the upper knuckles and the recorder's top plane. Weak, slightly warm bounce from the south wall preserves detail on the shadow side without creating another hard shadow. Hair casts a gentle edge at the jaw, and sleeves retain soft folds. Small contact shadows attach hands and the recorder to the tabletop and extend toward the south in world space; the stationary recorder retains a stationary contact shadow. Keep source positions, exposure and white balance steady. Matte surfaces produce subdued highlights rather than flashes. Changing the viewpoint must not relocate the light to the camera side.\\nUse a 40 mm-equivalent lens at seated eye height, in a medium composition with enough depth of field for the featured face, hands and recorder to remain legible. Focus stays on the featured person's eyes without a focus pull. The camera remains fixed throughout; position, orientation, focal length and framing stay unchanged. The foreground shoulder remains a narrow edge element, not a moving wipe or obstruction. Keep the same single shot from beginning to end.\\nThe output is one full-frame scene, with no reference panels, additional people, automatic captions or decorative overlays. Preserve the settled end pose for the adjacent reverse-angle cut.\\n\\noverall_soundscape:\\nLow steady ventilation and distant, muffled room ambience, with subtle breaths and fabric noise. The stationary recorder produces no playback, beeps or repeated scrape. Keep the room tone unobtrusive beneath the voice.\\n\\nnon_diegetic_music:\\nN/A"
    },
    "class_type": "PrimitiveStringMultiline",
    "_meta": {
      "title": "Input Text (Prompt)"
    }
  },
  "139": {
    "inputs": {
      "image": "2636c786c4c0e6c33db28ba14bbe1c381ed4f7cbd8ae925b745e370640e55fea.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "141": {
    "inputs": {
      "max_resolution": 1024,
      "jpeg_quality": 80,
      "suppress_default_preview": True,
      "preview_frames": [
        "131",
        1
      ],
      "preview_fps": 12,
      "tiny_vae": "taeh3.safetensors",
      "model": [
        "178",
        0
      ]
    },
    "class_type": "ModelPreviewOverrideKJ",
    "_meta": {
      "title": "Model Preview Override KJ"
    }
  },
  "147": {
    "inputs": {
      "lora_name": "minimax_h3_ref2v_turbo_8step_v1.0_768p_comfyui_bf16.safetensors",
      "strength_model": 1.0000000000000002,
      "model": [
        "127",
        0
      ]
    },
    "class_type": "LoraLoaderModelOnly",
    "_meta": {
      "title": "Load LoRA"
    }
  },
  "149": {
    "inputs": {
      "shift_video": 12,
      "shift_audio": 3,
      "model": [
        "147",
        0
      ]
    },
    "class_type": "MiniMaxH3SigmaShift",
    "_meta": {
      "title": "ModelSamplingMiniMaxH3"
    }
  },
  "178": {
    "inputs": {
      "attention": "comfy kitchen attention",
      "model": [
        "149",
        0
      ]
    },
    "class_type": "ModelAttentionBackend",
    "_meta": {
      "title": "ModelAttentionBackend"
    }
  },
  "208": {
    "inputs": {
      "step": 6,
      "sigmas": [
        "254",
        0
      ]
    },
    "class_type": "SplitSigmas",
    "_meta": {
      "title": "SplitSigmas"
    }
  },
  "209": {
    "inputs": {
      "noise": [
        "129",
        0
      ],
      "guider": [
        "126",
        0
      ],
      "sampler": [
        "123",
        0
      ],
      "sigmas": [
        "208",
        1
      ],
      "latent_image": [
        "212",
        0
      ]
    },
    "class_type": "SamplerCustomAdvanced",
    "_meta": {
      "title": "SamplerCustomAdvanced"
    }
  },
  "211": {
    "inputs": {
      "av_latent": [
        "125",
        1
      ]
    },
    "class_type": "LTXVSeparateAVLatent",
    "_meta": {
      "title": "Separate AV Latent"
    }
  },
  "212": {
    "inputs": {
      "video_latent": [
        "263",
        0
      ],
      "audio_latent": [
        "211",
        1
      ]
    },
    "class_type": "LTXVConcatAVLatent",
    "_meta": {
      "title": "Concat AV Latent"
    }
  },
  "218": {
    "inputs": {
      "samples": [
        "209",
        0
      ],
      "vae": [
        "120",
        0
      ]
    },
    "class_type": "VAEDecodeAudio",
    "_meta": {
      "title": "VAE Decode Audio"
    }
  },
  "219": {
    "inputs": {
      "samples": [
        "209",
        0
      ],
      "vae": [
        "119",
        0
      ]
    },
    "class_type": "VAEDecode",
    "_meta": {
      "title": "VAE Decode"
    }
  },
  "254": {
    "inputs": {
      "extra_steps": 1,
      "start_at_sigma": 0.7,
      "end_at_sigma": 0,
      "spacing": "cosine",
      "sigmas": [
        "124",
        0
      ]
    },
    "class_type": "H3SigmaRefiner",
    "_meta": {
      "title": "H3 Sigma Refiner"
    }
  },
  "256": {
    "inputs": {
      "image": "07d2e1d22673808899bba100354351b0d4b5b723a10358c7a9ffe92ec0c98ddc.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "257": {
    "inputs": {
      "image": "56a596334282d0057a0847e7a1f2714e8aa27725718b5a162e3ac33c02e42b17.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "258": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "259": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "260": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "263": {
    "inputs": {
      "model_name": "minimax_h3_latent_upscaler_3d_fp16.safetensors",
      "mode": "scale by multiplier",
      "mode.scale": 2,
      "align": 32,
      "device": "cuda",
      "precision": "fp16",
      "enable_chunking": True,
      "latent": [
        "211",
        0
      ]
    },
    "class_type": "MinimaxH3LatentUpscaler3D",
    "_meta": {
      "title": "Minimax H3 Latent Upscaler (3D)"
    }
  },
  "271": {
    "inputs": {
      "frame_rate": 24,
      "loop_count": 0,
      "filename_prefix": "第二次采样",
      "format": "video/h264-mp4",
      "pix_fmt": "yuv420p",
      "crf": 19,
      "save_metadata": True,
      "trim_to_audio": False,
      "pingpong": False,
      "save_output": True,
      "no_preview": False,
      "images": [
        "219",
        0
      ],
      "audio": [
        "218",
        0
      ]
    },
    "class_type": "VHS_VideoCombine",
    "_meta": {
      "title": "Video Combine 🎥🅥🅗🅢"
    }
  },
  "272": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "273": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "274": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "275": {
    "inputs": {
      "audio": "0ea9bca3948a0baf7983804066a8884203e6452b1c37a109bf6e5dc24e616996.flac",
      "audioUI": ""
    },
    "class_type": "LoadAudio",
    "_meta": {
      "title": "Load Audio"
    }
  }
}

# minimax_h3 2张图片加上1个参考音频
minimax_h3_2_image_1_audio_json = {
  "115": {
    "inputs": {
      "aspect_ratio": "16:9 (Widescreen)",
      "megapixels": 0.5,
      "multiple": 32
    },
    "class_type": "ResolutionSelector",
    "_meta": {
      "title": "PASS1 / 16:9 / 0.5MP"
    }
  },
  "119": {
    "inputs": {
      "vae_name": "minimax_h3_video_vae_fp16.safetensors"
    },
    "class_type": "VAELoader",
    "_meta": {
      "title": "Load VAE"
    }
  },
  "120": {
    "inputs": {
      "vae_name": "minimax_h3_audio_vae_fp32.safetensors"
    },
    "class_type": "VAELoader",
    "_meta": {
      "title": "Load VAE"
    }
  },
  "123": {
    "inputs": {
      "sampler_name": "euler"
    },
    "class_type": "KSamplerSelect",
    "_meta": {
      "title": "KSamplerSelect"
    }
  },
  "124": {
    "inputs": {
      "scheduler": "simple",
      "steps": 10,
      "denoise": 1,
      "model": [
        "141",
        0
      ]
    },
    "class_type": "BasicScheduler",
    "_meta": {
      "title": "BasicScheduler"
    }
  },
  "125": {
    "inputs": {
      "noise": [
        "129",
        0
      ],
      "guider": [
        "126",
        0
      ],
      "sampler": [
        "123",
        0
      ],
      "sigmas": [
        "208",
        0
      ],
      "latent_image": [
        "136",
        1
      ]
    },
    "class_type": "SamplerCustomAdvanced",
    "_meta": {
      "title": "SamplerCustomAdvanced"
    }
  },
  "126": {
    "inputs": {
      "model": [
        "141",
        0
      ],
      "conditioning": [
        "136",
        0
      ]
    },
    "class_type": "BasicGuider",
    "_meta": {
      "title": "Basic Guider"
    }
  },
  "127": {
    "inputs": {
      "unet_name": "minimax_h3_hybrid_fl2va_ref2va_b25-49-int8.safetensors",
      "weight_dtype": "default"
    },
    "class_type": "UNETLoader",
    "_meta": {
      "title": "Load Diffusion Model"
    }
  },
  "128": {
    "inputs": {
      "clip_name": "qwen3vl_32b_minimax_h3_int8_convrot.safetensors",
      "type": "minimax",
      "device": "default"
    },
    "class_type": "CLIPLoader",
    "_meta": {
      "title": "Load CLIP"
    }
  },
  "129": {
    "inputs": {
      "noise_seed": 999
    },
    "class_type": "RandomNoise",
    "_meta": {
      "title": "RandomNoise"
    }
  },
  "131": {
    "inputs": {
      "expression": "max(5, round(a * 24)) + (5 - (max(5, round(a * 24)) % 17)) % 17",
      "values.a": [
        "132",
        0
      ]
    },
    "class_type": "ComfyMathExpression",
    "_meta": {
      "title": "Math Expression"
    }
  },
  "132": {
    "inputs": {
      "value": 6
    },
    "class_type": "PrimitiveFloat",
    "_meta": {
      "title": "Float (Duration)"
    }
  },
  "136": {
    "inputs": {
      "prompt": [
        "138",
        0
      ],
      "width": [
        "115",
        0
      ],
      "height": [
        "115",
        1
      ],
      "length": [
        "131",
        1
      ],
      "task_type": "auto",
      "audio_mode": "native",
      "audio_denoise_strength": 1,
      "add_source_as_reference": False,
      "prompt_primary_audio_ordinal": 0,
      "strict_prompt_tags": True,
      "ref_image_size": "match",
      "reference_video_policy": "official_2_to_15s",
      "allow_above_reference_area": True,
      "clip": [
        "128",
        0
      ],
      "video_vae": [
        "119",
        0
      ],
      "audio_vae": [
        "120",
        0
      ],
      "ref_images.ref_image_0": [
        "139",
        0
      ],
      "ref_images.ref_image_1": [
        "256",
        0
      ],
      "ref_audios.ref_audio_0": [
        "275",
        0
      ]
    },
    "class_type": "MiniMaxH3AudioConditioningT8",
    "_meta": {
      "title": "T8 条件节点｜通用模式"
    }
  },
  "138": {
    "inputs": {
      "value": "subject_definitions:\\n<Subject 1> is Lin Che from <Picture 1>, a 29-year-old Chinese woman with a chin-length black bob, a small mole at the outer end of her left eyebrow, a dark red buttoned knitted cardigan over a white crew-neck top and black trousers. Preserve her facial identity, natural skin and wardrobe; the three standing views do not dictate her seated performance.\\n<Subject 2> is Chen Li from <Picture 2>, a 48-year-old Chinese man with a square face, short black hair graying at the temples, a slight gap in his right eyebrow, a medium-gray knitted cardigan over a pale blue shirt and dark gray trousers. Preserve his face, age, hair and clothing, not the reference pose.\\n<Subject 3> is the same empty meeting room from <Picture 3>: a matte light-gray rectangular table with its long axis east-west, one chair at each east and west short end, a closed high frosted window in the north wall, a low dark-green six-cubby cabinet against the west wall and a closed brown door in the south wall. Preserve the world-space layout and matte surfaces. Omit the four-view borders, reference viewpoints and incidental objects; the room contains only the two directed people and the one directed recorder.\\n\\nsummary:\\n[reference generation] A 6-second continuous live-action medium shot in <Subject 3>. Lin Che establishes that the recorder is already running and challenges Chen Li to speak on record. The three pictures supply identity and room design, with newly directed framing rather than exact endpoints.\\n\\nretention_analysis:\\n<Subject 1> (appears in [Shot 1]): fully_preserved - Keep Lin Che's identity, bob, dark red cardigan and white inner top while directing the specified seated performance.\\n<Subject 2> (appears in [Shot 1]): fully_preserved - Keep Chen Li's identity, gray temples, gray cardigan and pale blue shirt; the directed seated pose replaces the standing reference.\\n<Subject 3> (appears in [Shot 1]): partially_preserved - Keep the fixed room topology, north-window light, west cabinet and table material; omit multi-view panels and reference framing. The initial camera composition is newly directed.\\n\\ndetailed_description:\\nThe target video is a restrained contemporary Chinese live-action suspense drama, with natural skin texture, readable faces and softly lit matte surfaces.\\n[Shot 1] The camera occupies the open southeast aisle at approximately (1.5,-1.5,1.3) meters relative to the table center and faces northwest toward <Subject 1>. She is seated at the west end on screen-left, torso and head turned east toward <Subject 2>, with her gaze going screen-right. Her chin-length bob, natural eyebrow mark and dark red cardigan remain visible. His gray-clad shoulder and pale blue collar occupy only the extreme right foreground; his body remains at the east seat, and his shoulder does not obscure her face, hands or the recorder. The background shows the west green cabinet and only a geometrically plausible part of the north wall and window. The south door stays behind the camera and out of frame.\\nBoth remain seated on the same two chairs, feet on the floor, with neither changing seats or turning away. <Subject 1>'s two empty hands rest separately on the west table edge; <Subject 2>'s left hand rests on the east edge. There is exactly one small black rectangular audio recorder, about 10 by 3 by 1 centimeters, lying flat on the matte tabletop, long axis east-west and its single red indicator steadily lit. It has no readable display. Its center is 0.35 meters east and 0.12 meters south of the table center. His right fingertips rest on the tabletop three centimeters east of the recorder, separated from its casing. The recorder and both hands remain still until any explicitly directed action.\\nHold the initial pose for about one second. <Subject 1> (S1), using a clear low young-adult female Mandarin voice, measured and direct, says <d>[Chinese] 录音开着。你还要我关掉？</d> The statement about recording is a condition of this conversation, not a command to press a button. Finish speaking by about 4.5 seconds, close the mouth and hold eye contact for the remaining beat. Only speech-related lips, small facial tension and natural breathing change. The listener keeps a closed mouth and still hands. No control is pressed, and the indicator remains steadily red.\\nThe sole key is diffused cool-neutral daylight from the fixed high north window, above seated eye level. It softly illuminates the north-facing cheek, the upper knuckles and the recorder's top plane. Weak, slightly warm bounce from the south wall preserves detail on the shadow side without creating another hard shadow. Hair casts a gentle edge at the jaw, and sleeves retain soft folds. Small contact shadows attach hands and the recorder to the tabletop and extend toward the south in world space; the stationary recorder retains a stationary contact shadow. Keep source positions, exposure and white balance steady. Matte surfaces produce subdued highlights rather than flashes. Changing the viewpoint must not relocate the light to the camera side.\\nUse a 40 mm-equivalent lens at seated eye height, in a medium composition with enough depth of field for the featured face, hands and recorder to remain legible. Focus stays on the featured person's eyes without a focus pull. The camera remains fixed throughout; position, orientation, focal length and framing stay unchanged. The foreground shoulder remains a narrow edge element, not a moving wipe or obstruction. Keep the same single shot from beginning to end.\\nThe output is one full-frame scene, with no reference panels, additional people, automatic captions or decorative overlays. Preserve the settled end pose for the adjacent reverse-angle cut.\\n\\noverall_soundscape:\\nLow steady ventilation and distant, muffled room ambience, with subtle breaths and fabric noise. The stationary recorder produces no playback, beeps or repeated scrape. Keep the room tone unobtrusive beneath the voice.\\n\\nnon_diegetic_music:\\nN/A"
    },
    "class_type": "PrimitiveStringMultiline",
    "_meta": {
      "title": "Input Text (Prompt)"
    }
  },
  "139": {
    "inputs": {
      "image": "2636c786c4c0e6c33db28ba14bbe1c381ed4f7cbd8ae925b745e370640e55fea.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "141": {
    "inputs": {
      "max_resolution": 1024,
      "jpeg_quality": 80,
      "suppress_default_preview": True,
      "preview_frames": [
        "131",
        1
      ],
      "preview_fps": 12,
      "tiny_vae": "taeh3.safetensors",
      "model": [
        "178",
        0
      ]
    },
    "class_type": "ModelPreviewOverrideKJ",
    "_meta": {
      "title": "Model Preview Override KJ"
    }
  },
  "147": {
    "inputs": {
      "lora_name": "minimax_h3_ref2v_turbo_8step_v1.0_768p_comfyui_bf16.safetensors",
      "strength_model": 1.0000000000000002,
      "model": [
        "127",
        0
      ]
    },
    "class_type": "LoraLoaderModelOnly",
    "_meta": {
      "title": "Load LoRA"
    }
  },
  "149": {
    "inputs": {
      "shift_video": 12,
      "shift_audio": 3,
      "model": [
        "147",
        0
      ]
    },
    "class_type": "MiniMaxH3SigmaShift",
    "_meta": {
      "title": "ModelSamplingMiniMaxH3"
    }
  },
  "178": {
    "inputs": {
      "attention": "comfy kitchen attention",
      "model": [
        "149",
        0
      ]
    },
    "class_type": "ModelAttentionBackend",
    "_meta": {
      "title": "ModelAttentionBackend"
    }
  },
  "208": {
    "inputs": {
      "step": 6,
      "sigmas": [
        "254",
        0
      ]
    },
    "class_type": "SplitSigmas",
    "_meta": {
      "title": "SplitSigmas"
    }
  },
  "209": {
    "inputs": {
      "noise": [
        "129",
        0
      ],
      "guider": [
        "126",
        0
      ],
      "sampler": [
        "123",
        0
      ],
      "sigmas": [
        "208",
        1
      ],
      "latent_image": [
        "212",
        0
      ]
    },
    "class_type": "SamplerCustomAdvanced",
    "_meta": {
      "title": "SamplerCustomAdvanced"
    }
  },
  "211": {
    "inputs": {
      "av_latent": [
        "125",
        1
      ]
    },
    "class_type": "LTXVSeparateAVLatent",
    "_meta": {
      "title": "Separate AV Latent"
    }
  },
  "212": {
    "inputs": {
      "video_latent": [
        "263",
        0
      ],
      "audio_latent": [
        "211",
        1
      ]
    },
    "class_type": "LTXVConcatAVLatent",
    "_meta": {
      "title": "Concat AV Latent"
    }
  },
  "218": {
    "inputs": {
      "samples": [
        "209",
        0
      ],
      "vae": [
        "120",
        0
      ]
    },
    "class_type": "VAEDecodeAudio",
    "_meta": {
      "title": "VAE Decode Audio"
    }
  },
  "219": {
    "inputs": {
      "samples": [
        "209",
        0
      ],
      "vae": [
        "119",
        0
      ]
    },
    "class_type": "VAEDecode",
    "_meta": {
      "title": "VAE Decode"
    }
  },
  "254": {
    "inputs": {
      "extra_steps": 1,
      "start_at_sigma": 0.7,
      "end_at_sigma": 0,
      "spacing": "cosine",
      "sigmas": [
        "124",
        0
      ]
    },
    "class_type": "H3SigmaRefiner",
    "_meta": {
      "title": "H3 Sigma Refiner"
    }
  },
  "256": {
    "inputs": {
      "image": "07d2e1d22673808899bba100354351b0d4b5b723a10358c7a9ffe92ec0c98ddc.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "257": {
    "inputs": {
      "image": "56a596334282d0057a0847e7a1f2714e8aa27725718b5a162e3ac33c02e42b17.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "258": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "259": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "260": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "263": {
    "inputs": {
      "model_name": "minimax_h3_latent_upscaler_3d_fp16.safetensors",
      "mode": "scale by multiplier",
      "mode.scale": 2,
      "align": 32,
      "device": "cuda",
      "precision": "fp16",
      "enable_chunking": True,
      "latent": [
        "211",
        0
      ]
    },
    "class_type": "MinimaxH3LatentUpscaler3D",
    "_meta": {
      "title": "Minimax H3 Latent Upscaler (3D)"
    }
  },
  "271": {
    "inputs": {
      "frame_rate": 24,
      "loop_count": 0,
      "filename_prefix": "第二次采样",
      "format": "video/h264-mp4",
      "pix_fmt": "yuv420p",
      "crf": 19,
      "save_metadata": True,
      "trim_to_audio": False,
      "pingpong": False,
      "save_output": True,
      "no_preview": False,
      "images": [
        "219",
        0
      ],
      "audio": [
        "218",
        0
      ]
    },
    "class_type": "VHS_VideoCombine",
    "_meta": {
      "title": "Video Combine 🎥🅥🅗🅢"
    }
  },
  "272": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "273": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "274": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "275": {
    "inputs": {
      "audio": "0ea9bca3948a0baf7983804066a8884203e6452b1c37a109bf6e5dc24e616996.flac",
      "audioUI": ""
    },
    "class_type": "LoadAudio",
    "_meta": {
      "title": "Load Audio"
    }
  }
}

# minimax_h3 1张图片加上1个参考音频
minimax_h3_1_image_1_audio_json = {
  "115": {
    "inputs": {
      "aspect_ratio": "16:9 (Widescreen)",
      "megapixels": 0.5,
      "multiple": 32
    },
    "class_type": "ResolutionSelector",
    "_meta": {
      "title": "PASS1 / 16:9 / 0.5MP"
    }
  },
  "119": {
    "inputs": {
      "vae_name": "minimax_h3_video_vae_fp16.safetensors"
    },
    "class_type": "VAELoader",
    "_meta": {
      "title": "Load VAE"
    }
  },
  "120": {
    "inputs": {
      "vae_name": "minimax_h3_audio_vae_fp32.safetensors"
    },
    "class_type": "VAELoader",
    "_meta": {
      "title": "Load VAE"
    }
  },
  "123": {
    "inputs": {
      "sampler_name": "euler"
    },
    "class_type": "KSamplerSelect",
    "_meta": {
      "title": "KSamplerSelect"
    }
  },
  "124": {
    "inputs": {
      "scheduler": "simple",
      "steps": 10,
      "denoise": 1,
      "model": [
        "141",
        0
      ]
    },
    "class_type": "BasicScheduler",
    "_meta": {
      "title": "BasicScheduler"
    }
  },
  "125": {
    "inputs": {
      "noise": [
        "129",
        0
      ],
      "guider": [
        "126",
        0
      ],
      "sampler": [
        "123",
        0
      ],
      "sigmas": [
        "208",
        0
      ],
      "latent_image": [
        "136",
        1
      ]
    },
    "class_type": "SamplerCustomAdvanced",
    "_meta": {
      "title": "SamplerCustomAdvanced"
    }
  },
  "126": {
    "inputs": {
      "model": [
        "141",
        0
      ],
      "conditioning": [
        "136",
        0
      ]
    },
    "class_type": "BasicGuider",
    "_meta": {
      "title": "Basic Guider"
    }
  },
  "127": {
    "inputs": {
      "unet_name": "minimax_h3_hybrid_fl2va_ref2va_b25-49-int8.safetensors",
      "weight_dtype": "default"
    },
    "class_type": "UNETLoader",
    "_meta": {
      "title": "Load Diffusion Model"
    }
  },
  "128": {
    "inputs": {
      "clip_name": "qwen3vl_32b_minimax_h3_int8_convrot.safetensors",
      "type": "minimax",
      "device": "default"
    },
    "class_type": "CLIPLoader",
    "_meta": {
      "title": "Load CLIP"
    }
  },
  "129": {
    "inputs": {
      "noise_seed": 999
    },
    "class_type": "RandomNoise",
    "_meta": {
      "title": "RandomNoise"
    }
  },
  "131": {
    "inputs": {
      "expression": "max(5, round(a * 24)) + (5 - (max(5, round(a * 24)) % 17)) % 17",
      "values.a": [
        "132",
        0
      ]
    },
    "class_type": "ComfyMathExpression",
    "_meta": {
      "title": "Math Expression"
    }
  },
  "132": {
    "inputs": {
      "value": 6
    },
    "class_type": "PrimitiveFloat",
    "_meta": {
      "title": "Float (Duration)"
    }
  },
  "136": {
    "inputs": {
      "prompt": [
        "138",
        0
      ],
      "width": [
        "115",
        0
      ],
      "height": [
        "115",
        1
      ],
      "length": [
        "131",
        1
      ],
      "task_type": "auto",
      "audio_mode": "native",
      "audio_denoise_strength": 1,
      "add_source_as_reference": False,
      "prompt_primary_audio_ordinal": 0,
      "strict_prompt_tags": True,
      "ref_image_size": "match",
      "reference_video_policy": "official_2_to_15s",
      "allow_above_reference_area": True,
      "clip": [
        "128",
        0
      ],
      "video_vae": [
        "119",
        0
      ],
      "audio_vae": [
        "120",
        0
      ],
      "ref_images.ref_image_0": [
        "139",
        0
      ],
      "ref_audios.ref_audio_0": [
        "275",
        0
      ]
    },
    "class_type": "MiniMaxH3AudioConditioningT8",
    "_meta": {
      "title": "T8 条件节点｜通用模式"
    }
  },
  "138": {
    "inputs": {
      "value": "subject_definitions:\\n<Subject 1> is Lin Che from <Picture 1>, a 29-year-old Chinese woman with a chin-length black bob, a small mole at the outer end of her left eyebrow, a dark red buttoned knitted cardigan over a white crew-neck top and black trousers. Preserve her facial identity, natural skin and wardrobe; the three standing views do not dictate her seated performance.\\n<Subject 2> is Chen Li from <Picture 2>, a 48-year-old Chinese man with a square face, short black hair graying at the temples, a slight gap in his right eyebrow, a medium-gray knitted cardigan over a pale blue shirt and dark gray trousers. Preserve his face, age, hair and clothing, not the reference pose.\\n<Subject 3> is the same empty meeting room from <Picture 3>: a matte light-gray rectangular table with its long axis east-west, one chair at each east and west short end, a closed high frosted window in the north wall, a low dark-green six-cubby cabinet against the west wall and a closed brown door in the south wall. Preserve the world-space layout and matte surfaces. Omit the four-view borders, reference viewpoints and incidental objects; the room contains only the two directed people and the one directed recorder.\\n\\nsummary:\\n[reference generation] A 6-second continuous live-action medium shot in <Subject 3>. Lin Che establishes that the recorder is already running and challenges Chen Li to speak on record. The three pictures supply identity and room design, with newly directed framing rather than exact endpoints.\\n\\nretention_analysis:\\n<Subject 1> (appears in [Shot 1]): fully_preserved - Keep Lin Che's identity, bob, dark red cardigan and white inner top while directing the specified seated performance.\\n<Subject 2> (appears in [Shot 1]): fully_preserved - Keep Chen Li's identity, gray temples, gray cardigan and pale blue shirt; the directed seated pose replaces the standing reference.\\n<Subject 3> (appears in [Shot 1]): partially_preserved - Keep the fixed room topology, north-window light, west cabinet and table material; omit multi-view panels and reference framing. The initial camera composition is newly directed.\\n\\ndetailed_description:\\nThe target video is a restrained contemporary Chinese live-action suspense drama, with natural skin texture, readable faces and softly lit matte surfaces.\\n[Shot 1] The camera occupies the open southeast aisle at approximately (1.5,-1.5,1.3) meters relative to the table center and faces northwest toward <Subject 1>. She is seated at the west end on screen-left, torso and head turned east toward <Subject 2>, with her gaze going screen-right. Her chin-length bob, natural eyebrow mark and dark red cardigan remain visible. His gray-clad shoulder and pale blue collar occupy only the extreme right foreground; his body remains at the east seat, and his shoulder does not obscure her face, hands or the recorder. The background shows the west green cabinet and only a geometrically plausible part of the north wall and window. The south door stays behind the camera and out of frame.\\nBoth remain seated on the same two chairs, feet on the floor, with neither changing seats or turning away. <Subject 1>'s two empty hands rest separately on the west table edge; <Subject 2>'s left hand rests on the east edge. There is exactly one small black rectangular audio recorder, about 10 by 3 by 1 centimeters, lying flat on the matte tabletop, long axis east-west and its single red indicator steadily lit. It has no readable display. Its center is 0.35 meters east and 0.12 meters south of the table center. His right fingertips rest on the tabletop three centimeters east of the recorder, separated from its casing. The recorder and both hands remain still until any explicitly directed action.\\nHold the initial pose for about one second. <Subject 1> (S1), using a clear low young-adult female Mandarin voice, measured and direct, says <d>[Chinese] 录音开着。你还要我关掉？</d> The statement about recording is a condition of this conversation, not a command to press a button. Finish speaking by about 4.5 seconds, close the mouth and hold eye contact for the remaining beat. Only speech-related lips, small facial tension and natural breathing change. The listener keeps a closed mouth and still hands. No control is pressed, and the indicator remains steadily red.\\nThe sole key is diffused cool-neutral daylight from the fixed high north window, above seated eye level. It softly illuminates the north-facing cheek, the upper knuckles and the recorder's top plane. Weak, slightly warm bounce from the south wall preserves detail on the shadow side without creating another hard shadow. Hair casts a gentle edge at the jaw, and sleeves retain soft folds. Small contact shadows attach hands and the recorder to the tabletop and extend toward the south in world space; the stationary recorder retains a stationary contact shadow. Keep source positions, exposure and white balance steady. Matte surfaces produce subdued highlights rather than flashes. Changing the viewpoint must not relocate the light to the camera side.\\nUse a 40 mm-equivalent lens at seated eye height, in a medium composition with enough depth of field for the featured face, hands and recorder to remain legible. Focus stays on the featured person's eyes without a focus pull. The camera remains fixed throughout; position, orientation, focal length and framing stay unchanged. The foreground shoulder remains a narrow edge element, not a moving wipe or obstruction. Keep the same single shot from beginning to end.\\nThe output is one full-frame scene, with no reference panels, additional people, automatic captions or decorative overlays. Preserve the settled end pose for the adjacent reverse-angle cut.\\n\\noverall_soundscape:\\nLow steady ventilation and distant, muffled room ambience, with subtle breaths and fabric noise. The stationary recorder produces no playback, beeps or repeated scrape. Keep the room tone unobtrusive beneath the voice.\\n\\nnon_diegetic_music:\\nN/A"
    },
    "class_type": "PrimitiveStringMultiline",
    "_meta": {
      "title": "Input Text (Prompt)"
    }
  },
  "139": {
    "inputs": {
      "image": "2636c786c4c0e6c33db28ba14bbe1c381ed4f7cbd8ae925b745e370640e55fea.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "141": {
    "inputs": {
      "max_resolution": 1024,
      "jpeg_quality": 80,
      "suppress_default_preview": True,
      "preview_frames": [
        "131",
        1
      ],
      "preview_fps": 12,
      "tiny_vae": "taeh3.safetensors",
      "model": [
        "178",
        0
      ]
    },
    "class_type": "ModelPreviewOverrideKJ",
    "_meta": {
      "title": "Model Preview Override KJ"
    }
  },
  "147": {
    "inputs": {
      "lora_name": "minimax_h3_ref2v_turbo_8step_v1.0_768p_comfyui_bf16.safetensors",
      "strength_model": 1.0000000000000002,
      "model": [
        "127",
        0
      ]
    },
    "class_type": "LoraLoaderModelOnly",
    "_meta": {
      "title": "Load LoRA"
    }
  },
  "149": {
    "inputs": {
      "shift_video": 12,
      "shift_audio": 3,
      "model": [
        "147",
        0
      ]
    },
    "class_type": "MiniMaxH3SigmaShift",
    "_meta": {
      "title": "ModelSamplingMiniMaxH3"
    }
  },
  "178": {
    "inputs": {
      "attention": "comfy kitchen attention",
      "model": [
        "149",
        0
      ]
    },
    "class_type": "ModelAttentionBackend",
    "_meta": {
      "title": "ModelAttentionBackend"
    }
  },
  "208": {
    "inputs": {
      "step": 6,
      "sigmas": [
        "254",
        0
      ]
    },
    "class_type": "SplitSigmas",
    "_meta": {
      "title": "SplitSigmas"
    }
  },
  "209": {
    "inputs": {
      "noise": [
        "129",
        0
      ],
      "guider": [
        "126",
        0
      ],
      "sampler": [
        "123",
        0
      ],
      "sigmas": [
        "208",
        1
      ],
      "latent_image": [
        "212",
        0
      ]
    },
    "class_type": "SamplerCustomAdvanced",
    "_meta": {
      "title": "SamplerCustomAdvanced"
    }
  },
  "211": {
    "inputs": {
      "av_latent": [
        "125",
        1
      ]
    },
    "class_type": "LTXVSeparateAVLatent",
    "_meta": {
      "title": "Separate AV Latent"
    }
  },
  "212": {
    "inputs": {
      "video_latent": [
        "263",
        0
      ],
      "audio_latent": [
        "211",
        1
      ]
    },
    "class_type": "LTXVConcatAVLatent",
    "_meta": {
      "title": "Concat AV Latent"
    }
  },
  "218": {
    "inputs": {
      "samples": [
        "209",
        0
      ],
      "vae": [
        "120",
        0
      ]
    },
    "class_type": "VAEDecodeAudio",
    "_meta": {
      "title": "VAE Decode Audio"
    }
  },
  "219": {
    "inputs": {
      "samples": [
        "209",
        0
      ],
      "vae": [
        "119",
        0
      ]
    },
    "class_type": "VAEDecode",
    "_meta": {
      "title": "VAE Decode"
    }
  },
  "254": {
    "inputs": {
      "extra_steps": 1,
      "start_at_sigma": 0.7,
      "end_at_sigma": 0,
      "spacing": "cosine",
      "sigmas": [
        "124",
        0
      ]
    },
    "class_type": "H3SigmaRefiner",
    "_meta": {
      "title": "H3 Sigma Refiner"
    }
  },
  "256": {
    "inputs": {
      "image": "07d2e1d22673808899bba100354351b0d4b5b723a10358c7a9ffe92ec0c98ddc.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "257": {
    "inputs": {
      "image": "56a596334282d0057a0847e7a1f2714e8aa27725718b5a162e3ac33c02e42b17.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "258": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "259": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "260": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "263": {
    "inputs": {
      "model_name": "minimax_h3_latent_upscaler_3d_fp16.safetensors",
      "mode": "scale by multiplier",
      "mode.scale": 2,
      "align": 32,
      "device": "cuda",
      "precision": "fp16",
      "enable_chunking": True,
      "latent": [
        "211",
        0
      ]
    },
    "class_type": "MinimaxH3LatentUpscaler3D",
    "_meta": {
      "title": "Minimax H3 Latent Upscaler (3D)"
    }
  },
  "271": {
    "inputs": {
      "frame_rate": 24,
      "loop_count": 0,
      "filename_prefix": "第二次采样",
      "format": "video/h264-mp4",
      "pix_fmt": "yuv420p",
      "crf": 19,
      "save_metadata": True,
      "trim_to_audio": False,
      "pingpong": False,
      "save_output": True,
      "no_preview": False,
      "images": [
        "219",
        0
      ],
      "audio": [
        "218",
        0
      ]
    },
    "class_type": "VHS_VideoCombine",
    "_meta": {
      "title": "Video Combine 🎥🅥🅗🅢"
    }
  },
  "272": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "273": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "274": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "275": {
    "inputs": {
      "audio": "0ea9bca3948a0baf7983804066a8884203e6452b1c37a109bf6e5dc24e616996.flac",
      "audioUI": ""
    },
    "class_type": "LoadAudio",
    "_meta": {
      "title": "Load Audio"
    }
  }
}


# minimax_h3 9张图片参考
minimax_h3_9_image_json = {
  "115": {
    "inputs": {
      "aspect_ratio": "16:9 (Widescreen)",
      "megapixels": 0.5,
      "multiple": 32
    },
    "class_type": "ResolutionSelector",
    "_meta": {
      "title": "PASS1 / 16:9 / 0.5MP"
    }
  },
  "119": {
    "inputs": {
      "vae_name": "minimax_h3_video_vae_fp16.safetensors"
    },
    "class_type": "VAELoader",
    "_meta": {
      "title": "Load VAE"
    }
  },
  "120": {
    "inputs": {
      "vae_name": "minimax_h3_audio_vae_fp32.safetensors"
    },
    "class_type": "VAELoader",
    "_meta": {
      "title": "Load VAE"
    }
  },
  "123": {
    "inputs": {
      "sampler_name": "euler"
    },
    "class_type": "KSamplerSelect",
    "_meta": {
      "title": "KSamplerSelect"
    }
  },
  "124": {
    "inputs": {
      "scheduler": "simple",
      "steps": 10,
      "denoise": 1,
      "model": [
        "141",
        0
      ]
    },
    "class_type": "BasicScheduler",
    "_meta": {
      "title": "BasicScheduler"
    }
  },
  "125": {
    "inputs": {
      "noise": [
        "129",
        0
      ],
      "guider": [
        "126",
        0
      ],
      "sampler": [
        "123",
        0
      ],
      "sigmas": [
        "208",
        0
      ],
      "latent_image": [
        "136",
        1
      ]
    },
    "class_type": "SamplerCustomAdvanced",
    "_meta": {
      "title": "SamplerCustomAdvanced"
    }
  },
  "126": {
    "inputs": {
      "model": [
        "141",
        0
      ],
      "conditioning": [
        "136",
        0
      ]
    },
    "class_type": "BasicGuider",
    "_meta": {
      "title": "Basic Guider"
    }
  },
  "127": {
    "inputs": {
      "unet_name": "minimax_h3_hybrid_fl2va_ref2va_b25-49-int8.safetensors",
      "weight_dtype": "default"
    },
    "class_type": "UNETLoader",
    "_meta": {
      "title": "Load Diffusion Model"
    }
  },
  "128": {
    "inputs": {
      "clip_name": "qwen3vl_32b_minimax_h3_int8_convrot.safetensors",
      "type": "minimax",
      "device": "default"
    },
    "class_type": "CLIPLoader",
    "_meta": {
      "title": "Load CLIP"
    }
  },
  "129": {
    "inputs": {
      "noise_seed": 999
    },
    "class_type": "RandomNoise",
    "_meta": {
      "title": "RandomNoise"
    }
  },
  "131": {
    "inputs": {
      "expression": "max(5, round(a * 24)) + (5 - (max(5, round(a * 24)) % 17)) % 17",
      "values.a": [
        "132",
        0
      ]
    },
    "class_type": "ComfyMathExpression",
    "_meta": {
      "title": "Math Expression"
    }
  },
  "132": {
    "inputs": {
      "value": 6
    },
    "class_type": "PrimitiveFloat",
    "_meta": {
      "title": "Float (Duration)"
    }
  },
  "136": {
    "inputs": {
      "prompt": [
        "138",
        0
      ],
      "width": [
        "115",
        0
      ],
      "height": [
        "115",
        1
      ],
      "length": [
        "131",
        1
      ],
      "task_type": "auto",
      "audio_mode": "native",
      "audio_denoise_strength": 1,
      "add_source_as_reference": False,
      "prompt_primary_audio_ordinal": 0,
      "strict_prompt_tags": True,
      "ref_image_size": "match",
      "reference_video_policy": "official_2_to_15s",
      "allow_above_reference_area": True,
      "clip": [
        "128",
        0
      ],
      "video_vae": [
        "119",
        0
      ],
      "audio_vae": [
        "120",
        0
      ],
      "ref_images.ref_image_0": [
        "139",
        0
      ],
      "ref_images.ref_image_1": [
        "256",
        0
      ],
      "ref_images.ref_image_2": [
        "257",
        0
      ],
      "ref_images.ref_image_3": [
        "258",
        0
      ],
      "ref_images.ref_image_4": [
        "259",
        0
      ],
      "ref_images.ref_image_5": [
        "260",
        0
      ],
      "ref_images.ref_image_6": [
        "272",
        0
      ],
      "ref_images.ref_image_7": [
        "273",
        0
      ],
      "ref_images.ref_image_8": [
        "274",
        0
      ]
    },
    "class_type": "MiniMaxH3AudioConditioningT8",
    "_meta": {
      "title": "T8 条件节点｜通用模式"
    }
  },
  "138": {
    "inputs": {
      "value": "subject_definitions:\\n<Subject 1> is Lin Che from <Picture 1>, a 29-year-old Chinese woman with a chin-length black bob, a small mole at the outer end of her left eyebrow, a dark red buttoned knitted cardigan over a white crew-neck top and black trousers. Preserve her facial identity, natural skin and wardrobe; the three standing views do not dictate her seated performance.\\n<Subject 2> is Chen Li from <Picture 2>, a 48-year-old Chinese man with a square face, short black hair graying at the temples, a slight gap in his right eyebrow, a medium-gray knitted cardigan over a pale blue shirt and dark gray trousers. Preserve his face, age, hair and clothing, not the reference pose.\\n<Subject 3> is the same empty meeting room from <Picture 3>: a matte light-gray rectangular table with its long axis east-west, one chair at each east and west short end, a closed high frosted window in the north wall, a low dark-green six-cubby cabinet against the west wall and a closed brown door in the south wall. Preserve the world-space layout and matte surfaces. Omit the four-view borders, reference viewpoints and incidental objects; the room contains only the two directed people and the one directed recorder.\\n\\nsummary:\\n[reference generation] A 6-second continuous live-action medium shot in <Subject 3>. Lin Che establishes that the recorder is already running and challenges Chen Li to speak on record. The three pictures supply identity and room design, with newly directed framing rather than exact endpoints.\\n\\nretention_analysis:\\n<Subject 1> (appears in [Shot 1]): fully_preserved - Keep Lin Che's identity, bob, dark red cardigan and white inner top while directing the specified seated performance.\\n<Subject 2> (appears in [Shot 1]): fully_preserved - Keep Chen Li's identity, gray temples, gray cardigan and pale blue shirt; the directed seated pose replaces the standing reference.\\n<Subject 3> (appears in [Shot 1]): partially_preserved - Keep the fixed room topology, north-window light, west cabinet and table material; omit multi-view panels and reference framing. The initial camera composition is newly directed.\\n\\ndetailed_description:\\nThe target video is a restrained contemporary Chinese live-action suspense drama, with natural skin texture, readable faces and softly lit matte surfaces.\\n[Shot 1] The camera occupies the open southeast aisle at approximately (1.5,-1.5,1.3) meters relative to the table center and faces northwest toward <Subject 1>. She is seated at the west end on screen-left, torso and head turned east toward <Subject 2>, with her gaze going screen-right. Her chin-length bob, natural eyebrow mark and dark red cardigan remain visible. His gray-clad shoulder and pale blue collar occupy only the extreme right foreground; his body remains at the east seat, and his shoulder does not obscure her face, hands or the recorder. The background shows the west green cabinet and only a geometrically plausible part of the north wall and window. The south door stays behind the camera and out of frame.\\nBoth remain seated on the same two chairs, feet on the floor, with neither changing seats or turning away. <Subject 1>'s two empty hands rest separately on the west table edge; <Subject 2>'s left hand rests on the east edge. There is exactly one small black rectangular audio recorder, about 10 by 3 by 1 centimeters, lying flat on the matte tabletop, long axis east-west and its single red indicator steadily lit. It has no readable display. Its center is 0.35 meters east and 0.12 meters south of the table center. His right fingertips rest on the tabletop three centimeters east of the recorder, separated from its casing. The recorder and both hands remain still until any explicitly directed action.\\nHold the initial pose for about one second. <Subject 1> (S1), using a clear low young-adult female Mandarin voice, measured and direct, says <d>[Chinese] 录音开着。你还要我关掉？</d> The statement about recording is a condition of this conversation, not a command to press a button. Finish speaking by about 4.5 seconds, close the mouth and hold eye contact for the remaining beat. Only speech-related lips, small facial tension and natural breathing change. The listener keeps a closed mouth and still hands. No control is pressed, and the indicator remains steadily red.\\nThe sole key is diffused cool-neutral daylight from the fixed high north window, above seated eye level. It softly illuminates the north-facing cheek, the upper knuckles and the recorder's top plane. Weak, slightly warm bounce from the south wall preserves detail on the shadow side without creating another hard shadow. Hair casts a gentle edge at the jaw, and sleeves retain soft folds. Small contact shadows attach hands and the recorder to the tabletop and extend toward the south in world space; the stationary recorder retains a stationary contact shadow. Keep source positions, exposure and white balance steady. Matte surfaces produce subdued highlights rather than flashes. Changing the viewpoint must not relocate the light to the camera side.\\nUse a 40 mm-equivalent lens at seated eye height, in a medium composition with enough depth of field for the featured face, hands and recorder to remain legible. Focus stays on the featured person's eyes without a focus pull. The camera remains fixed throughout; position, orientation, focal length and framing stay unchanged. The foreground shoulder remains a narrow edge element, not a moving wipe or obstruction. Keep the same single shot from beginning to end.\\nThe output is one full-frame scene, with no reference panels, additional people, automatic captions or decorative overlays. Preserve the settled end pose for the adjacent reverse-angle cut.\\n\\noverall_soundscape:\\nLow steady ventilation and distant, muffled room ambience, with subtle breaths and fabric noise. The stationary recorder produces no playback, beeps or repeated scrape. Keep the room tone unobtrusive beneath the voice.\\n\\nnon_diegetic_music:\\nN/A"
    },
    "class_type": "PrimitiveStringMultiline",
    "_meta": {
      "title": "Input Text (Prompt)"
    }
  },
  "139": {
    "inputs": {
      "image": "2636c786c4c0e6c33db28ba14bbe1c381ed4f7cbd8ae925b745e370640e55fea.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "141": {
    "inputs": {
      "max_resolution": 1024,
      "jpeg_quality": 80,
      "suppress_default_preview": True,
      "preview_frames": [
        "131",
        1
      ],
      "preview_fps": 12,
      "tiny_vae": "taeh3.safetensors",
      "model": [
        "178",
        0
      ]
    },
    "class_type": "ModelPreviewOverrideKJ",
    "_meta": {
      "title": "Model Preview Override KJ"
    }
  },
  "147": {
    "inputs": {
      "lora_name": "minimax_h3_ref2v_turbo_8step_v1.0_768p_comfyui_bf16.safetensors",
      "strength_model": 1.0000000000000002,
      "model": [
        "127",
        0
      ]
    },
    "class_type": "LoraLoaderModelOnly",
    "_meta": {
      "title": "Load LoRA"
    }
  },
  "149": {
    "inputs": {
      "shift_video": 12,
      "shift_audio": 3,
      "model": [
        "147",
        0
      ]
    },
    "class_type": "MiniMaxH3SigmaShift",
    "_meta": {
      "title": "ModelSamplingMiniMaxH3"
    }
  },
  "178": {
    "inputs": {
      "attention": "comfy kitchen attention",
      "model": [
        "149",
        0
      ]
    },
    "class_type": "ModelAttentionBackend",
    "_meta": {
      "title": "ModelAttentionBackend"
    }
  },
  "208": {
    "inputs": {
      "step": 6,
      "sigmas": [
        "254",
        0
      ]
    },
    "class_type": "SplitSigmas",
    "_meta": {
      "title": "SplitSigmas"
    }
  },
  "209": {
    "inputs": {
      "noise": [
        "129",
        0
      ],
      "guider": [
        "126",
        0
      ],
      "sampler": [
        "123",
        0
      ],
      "sigmas": [
        "208",
        1
      ],
      "latent_image": [
        "212",
        0
      ]
    },
    "class_type": "SamplerCustomAdvanced",
    "_meta": {
      "title": "SamplerCustomAdvanced"
    }
  },
  "211": {
    "inputs": {
      "av_latent": [
        "125",
        1
      ]
    },
    "class_type": "LTXVSeparateAVLatent",
    "_meta": {
      "title": "Separate AV Latent"
    }
  },
  "212": {
    "inputs": {
      "video_latent": [
        "263",
        0
      ],
      "audio_latent": [
        "211",
        1
      ]
    },
    "class_type": "LTXVConcatAVLatent",
    "_meta": {
      "title": "Concat AV Latent"
    }
  },
  "218": {
    "inputs": {
      "samples": [
        "209",
        0
      ],
      "vae": [
        "120",
        0
      ]
    },
    "class_type": "VAEDecodeAudio",
    "_meta": {
      "title": "VAE Decode Audio"
    }
  },
  "219": {
    "inputs": {
      "samples": [
        "209",
        0
      ],
      "vae": [
        "119",
        0
      ]
    },
    "class_type": "VAEDecode",
    "_meta": {
      "title": "VAE Decode"
    }
  },
  "254": {
    "inputs": {
      "extra_steps": 1,
      "start_at_sigma": 0.7,
      "end_at_sigma": 0,
      "spacing": "cosine",
      "sigmas": [
        "124",
        0
      ]
    },
    "class_type": "H3SigmaRefiner",
    "_meta": {
      "title": "H3 Sigma Refiner"
    }
  },
  "256": {
    "inputs": {
      "image": "07d2e1d22673808899bba100354351b0d4b5b723a10358c7a9ffe92ec0c98ddc.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "257": {
    "inputs": {
      "image": "56a596334282d0057a0847e7a1f2714e8aa27725718b5a162e3ac33c02e42b17.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "258": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "259": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "260": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "263": {
    "inputs": {
      "model_name": "minimax_h3_latent_upscaler_3d_fp16.safetensors",
      "mode": "scale by multiplier",
      "mode.scale": 2,
      "align": 32,
      "device": "cuda",
      "precision": "fp16",
      "enable_chunking": True,
      "latent": [
        "211",
        0
      ]
    },
    "class_type": "MinimaxH3LatentUpscaler3D",
    "_meta": {
      "title": "Minimax H3 Latent Upscaler (3D)"
    }
  },
  "271": {
    "inputs": {
      "frame_rate": 24,
      "loop_count": 0,
      "filename_prefix": "第二次采样",
      "format": "video/h264-mp4",
      "pix_fmt": "yuv420p",
      "crf": 19,
      "save_metadata": True,
      "trim_to_audio": False,
      "pingpong": False,
      "save_output": True,
      "no_preview": False,
      "images": [
        "219",
        0
      ],
      "audio": [
        "218",
        0
      ]
    },
    "class_type": "VHS_VideoCombine",
    "_meta": {
      "title": "Video Combine 🎥🅥🅗🅢"
    }
  },
  "272": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "273": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "274": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "275": {
    "inputs": {
      "audio": "0ea9bca3948a0baf7983804066a8884203e6452b1c37a109bf6e5dc24e616996.flac",
      "audioUI": ""
    },
    "class_type": "LoadAudio",
    "_meta": {
      "title": "Load Audio"
    }
  }
}

# minimax_h3 8张图片个参考
minimax_h3_8_image_json = {
  "115": {
    "inputs": {
      "aspect_ratio": "16:9 (Widescreen)",
      "megapixels": 0.5,
      "multiple": 32
    },
    "class_type": "ResolutionSelector",
    "_meta": {
      "title": "PASS1 / 16:9 / 0.5MP"
    }
  },
  "119": {
    "inputs": {
      "vae_name": "minimax_h3_video_vae_fp16.safetensors"
    },
    "class_type": "VAELoader",
    "_meta": {
      "title": "Load VAE"
    }
  },
  "120": {
    "inputs": {
      "vae_name": "minimax_h3_audio_vae_fp32.safetensors"
    },
    "class_type": "VAELoader",
    "_meta": {
      "title": "Load VAE"
    }
  },
  "123": {
    "inputs": {
      "sampler_name": "euler"
    },
    "class_type": "KSamplerSelect",
    "_meta": {
      "title": "KSamplerSelect"
    }
  },
  "124": {
    "inputs": {
      "scheduler": "simple",
      "steps": 10,
      "denoise": 1,
      "model": [
        "141",
        0
      ]
    },
    "class_type": "BasicScheduler",
    "_meta": {
      "title": "BasicScheduler"
    }
  },
  "125": {
    "inputs": {
      "noise": [
        "129",
        0
      ],
      "guider": [
        "126",
        0
      ],
      "sampler": [
        "123",
        0
      ],
      "sigmas": [
        "208",
        0
      ],
      "latent_image": [
        "136",
        1
      ]
    },
    "class_type": "SamplerCustomAdvanced",
    "_meta": {
      "title": "SamplerCustomAdvanced"
    }
  },
  "126": {
    "inputs": {
      "model": [
        "141",
        0
      ],
      "conditioning": [
        "136",
        0
      ]
    },
    "class_type": "BasicGuider",
    "_meta": {
      "title": "Basic Guider"
    }
  },
  "127": {
    "inputs": {
      "unet_name": "minimax_h3_hybrid_fl2va_ref2va_b25-49-int8.safetensors",
      "weight_dtype": "default"
    },
    "class_type": "UNETLoader",
    "_meta": {
      "title": "Load Diffusion Model"
    }
  },
  "128": {
    "inputs": {
      "clip_name": "qwen3vl_32b_minimax_h3_int8_convrot.safetensors",
      "type": "minimax",
      "device": "default"
    },
    "class_type": "CLIPLoader",
    "_meta": {
      "title": "Load CLIP"
    }
  },
  "129": {
    "inputs": {
      "noise_seed": 999
    },
    "class_type": "RandomNoise",
    "_meta": {
      "title": "RandomNoise"
    }
  },
  "131": {
    "inputs": {
      "expression": "max(5, round(a * 24)) + (5 - (max(5, round(a * 24)) % 17)) % 17",
      "values.a": [
        "132",
        0
      ]
    },
    "class_type": "ComfyMathExpression",
    "_meta": {
      "title": "Math Expression"
    }
  },
  "132": {
    "inputs": {
      "value": 6
    },
    "class_type": "PrimitiveFloat",
    "_meta": {
      "title": "Float (Duration)"
    }
  },
  "136": {
    "inputs": {
      "prompt": [
        "138",
        0
      ],
      "width": [
        "115",
        0
      ],
      "height": [
        "115",
        1
      ],
      "length": [
        "131",
        1
      ],
      "task_type": "auto",
      "audio_mode": "native",
      "audio_denoise_strength": 1,
      "add_source_as_reference": False,
      "prompt_primary_audio_ordinal": 0,
      "strict_prompt_tags": True,
      "ref_image_size": "match",
      "reference_video_policy": "official_2_to_15s",
      "allow_above_reference_area": True,
      "clip": [
        "128",
        0
      ],
      "video_vae": [
        "119",
        0
      ],
      "audio_vae": [
        "120",
        0
      ],
      "ref_images.ref_image_0": [
        "139",
        0
      ],
      "ref_images.ref_image_1": [
        "256",
        0
      ],
      "ref_images.ref_image_2": [
        "257",
        0
      ],
      "ref_images.ref_image_3": [
        "258",
        0
      ],
      "ref_images.ref_image_4": [
        "259",
        0
      ],
      "ref_images.ref_image_5": [
        "260",
        0
      ],
      "ref_images.ref_image_6": [
        "272",
        0
      ],
      "ref_images.ref_image_7": [
        "273",
        0
      ]
    },
    "class_type": "MiniMaxH3AudioConditioningT8",
    "_meta": {
      "title": "T8 条件节点｜通用模式"
    }
  },
  "138": {
    "inputs": {
      "value": "subject_definitions:\\n<Subject 1> is Lin Che from <Picture 1>, a 29-year-old Chinese woman with a chin-length black bob, a small mole at the outer end of her left eyebrow, a dark red buttoned knitted cardigan over a white crew-neck top and black trousers. Preserve her facial identity, natural skin and wardrobe; the three standing views do not dictate her seated performance.\\n<Subject 2> is Chen Li from <Picture 2>, a 48-year-old Chinese man with a square face, short black hair graying at the temples, a slight gap in his right eyebrow, a medium-gray knitted cardigan over a pale blue shirt and dark gray trousers. Preserve his face, age, hair and clothing, not the reference pose.\\n<Subject 3> is the same empty meeting room from <Picture 3>: a matte light-gray rectangular table with its long axis east-west, one chair at each east and west short end, a closed high frosted window in the north wall, a low dark-green six-cubby cabinet against the west wall and a closed brown door in the south wall. Preserve the world-space layout and matte surfaces. Omit the four-view borders, reference viewpoints and incidental objects; the room contains only the two directed people and the one directed recorder.\\n\\nsummary:\\n[reference generation] A 6-second continuous live-action medium shot in <Subject 3>. Lin Che establishes that the recorder is already running and challenges Chen Li to speak on record. The three pictures supply identity and room design, with newly directed framing rather than exact endpoints.\\n\\nretention_analysis:\\n<Subject 1> (appears in [Shot 1]): fully_preserved - Keep Lin Che's identity, bob, dark red cardigan and white inner top while directing the specified seated performance.\\n<Subject 2> (appears in [Shot 1]): fully_preserved - Keep Chen Li's identity, gray temples, gray cardigan and pale blue shirt; the directed seated pose replaces the standing reference.\\n<Subject 3> (appears in [Shot 1]): partially_preserved - Keep the fixed room topology, north-window light, west cabinet and table material; omit multi-view panels and reference framing. The initial camera composition is newly directed.\\n\\ndetailed_description:\\nThe target video is a restrained contemporary Chinese live-action suspense drama, with natural skin texture, readable faces and softly lit matte surfaces.\\n[Shot 1] The camera occupies the open southeast aisle at approximately (1.5,-1.5,1.3) meters relative to the table center and faces northwest toward <Subject 1>. She is seated at the west end on screen-left, torso and head turned east toward <Subject 2>, with her gaze going screen-right. Her chin-length bob, natural eyebrow mark and dark red cardigan remain visible. His gray-clad shoulder and pale blue collar occupy only the extreme right foreground; his body remains at the east seat, and his shoulder does not obscure her face, hands or the recorder. The background shows the west green cabinet and only a geometrically plausible part of the north wall and window. The south door stays behind the camera and out of frame.\\nBoth remain seated on the same two chairs, feet on the floor, with neither changing seats or turning away. <Subject 1>'s two empty hands rest separately on the west table edge; <Subject 2>'s left hand rests on the east edge. There is exactly one small black rectangular audio recorder, about 10 by 3 by 1 centimeters, lying flat on the matte tabletop, long axis east-west and its single red indicator steadily lit. It has no readable display. Its center is 0.35 meters east and 0.12 meters south of the table center. His right fingertips rest on the tabletop three centimeters east of the recorder, separated from its casing. The recorder and both hands remain still until any explicitly directed action.\\nHold the initial pose for about one second. <Subject 1> (S1), using a clear low young-adult female Mandarin voice, measured and direct, says <d>[Chinese] 录音开着。你还要我关掉？</d> The statement about recording is a condition of this conversation, not a command to press a button. Finish speaking by about 4.5 seconds, close the mouth and hold eye contact for the remaining beat. Only speech-related lips, small facial tension and natural breathing change. The listener keeps a closed mouth and still hands. No control is pressed, and the indicator remains steadily red.\\nThe sole key is diffused cool-neutral daylight from the fixed high north window, above seated eye level. It softly illuminates the north-facing cheek, the upper knuckles and the recorder's top plane. Weak, slightly warm bounce from the south wall preserves detail on the shadow side without creating another hard shadow. Hair casts a gentle edge at the jaw, and sleeves retain soft folds. Small contact shadows attach hands and the recorder to the tabletop and extend toward the south in world space; the stationary recorder retains a stationary contact shadow. Keep source positions, exposure and white balance steady. Matte surfaces produce subdued highlights rather than flashes. Changing the viewpoint must not relocate the light to the camera side.\\nUse a 40 mm-equivalent lens at seated eye height, in a medium composition with enough depth of field for the featured face, hands and recorder to remain legible. Focus stays on the featured person's eyes without a focus pull. The camera remains fixed throughout; position, orientation, focal length and framing stay unchanged. The foreground shoulder remains a narrow edge element, not a moving wipe or obstruction. Keep the same single shot from beginning to end.\\nThe output is one full-frame scene, with no reference panels, additional people, automatic captions or decorative overlays. Preserve the settled end pose for the adjacent reverse-angle cut.\\n\\noverall_soundscape:\\nLow steady ventilation and distant, muffled room ambience, with subtle breaths and fabric noise. The stationary recorder produces no playback, beeps or repeated scrape. Keep the room tone unobtrusive beneath the voice.\\n\\nnon_diegetic_music:\\nN/A"
    },
    "class_type": "PrimitiveStringMultiline",
    "_meta": {
      "title": "Input Text (Prompt)"
    }
  },
  "139": {
    "inputs": {
      "image": "2636c786c4c0e6c33db28ba14bbe1c381ed4f7cbd8ae925b745e370640e55fea.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "141": {
    "inputs": {
      "max_resolution": 1024,
      "jpeg_quality": 80,
      "suppress_default_preview": True,
      "preview_frames": [
        "131",
        1
      ],
      "preview_fps": 12,
      "tiny_vae": "taeh3.safetensors",
      "model": [
        "178",
        0
      ]
    },
    "class_type": "ModelPreviewOverrideKJ",
    "_meta": {
      "title": "Model Preview Override KJ"
    }
  },
  "147": {
    "inputs": {
      "lora_name": "minimax_h3_ref2v_turbo_8step_v1.0_768p_comfyui_bf16.safetensors",
      "strength_model": 1.0000000000000002,
      "model": [
        "127",
        0
      ]
    },
    "class_type": "LoraLoaderModelOnly",
    "_meta": {
      "title": "Load LoRA"
    }
  },
  "149": {
    "inputs": {
      "shift_video": 12,
      "shift_audio": 3,
      "model": [
        "147",
        0
      ]
    },
    "class_type": "MiniMaxH3SigmaShift",
    "_meta": {
      "title": "ModelSamplingMiniMaxH3"
    }
  },
  "178": {
    "inputs": {
      "attention": "comfy kitchen attention",
      "model": [
        "149",
        0
      ]
    },
    "class_type": "ModelAttentionBackend",
    "_meta": {
      "title": "ModelAttentionBackend"
    }
  },
  "208": {
    "inputs": {
      "step": 6,
      "sigmas": [
        "254",
        0
      ]
    },
    "class_type": "SplitSigmas",
    "_meta": {
      "title": "SplitSigmas"
    }
  },
  "209": {
    "inputs": {
      "noise": [
        "129",
        0
      ],
      "guider": [
        "126",
        0
      ],
      "sampler": [
        "123",
        0
      ],
      "sigmas": [
        "208",
        1
      ],
      "latent_image": [
        "212",
        0
      ]
    },
    "class_type": "SamplerCustomAdvanced",
    "_meta": {
      "title": "SamplerCustomAdvanced"
    }
  },
  "211": {
    "inputs": {
      "av_latent": [
        "125",
        1
      ]
    },
    "class_type": "LTXVSeparateAVLatent",
    "_meta": {
      "title": "Separate AV Latent"
    }
  },
  "212": {
    "inputs": {
      "video_latent": [
        "263",
        0
      ],
      "audio_latent": [
        "211",
        1
      ]
    },
    "class_type": "LTXVConcatAVLatent",
    "_meta": {
      "title": "Concat AV Latent"
    }
  },
  "218": {
    "inputs": {
      "samples": [
        "209",
        0
      ],
      "vae": [
        "120",
        0
      ]
    },
    "class_type": "VAEDecodeAudio",
    "_meta": {
      "title": "VAE Decode Audio"
    }
  },
  "219": {
    "inputs": {
      "samples": [
        "209",
        0
      ],
      "vae": [
        "119",
        0
      ]
    },
    "class_type": "VAEDecode",
    "_meta": {
      "title": "VAE Decode"
    }
  },
  "254": {
    "inputs": {
      "extra_steps": 1,
      "start_at_sigma": 0.7,
      "end_at_sigma": 0,
      "spacing": "cosine",
      "sigmas": [
        "124",
        0
      ]
    },
    "class_type": "H3SigmaRefiner",
    "_meta": {
      "title": "H3 Sigma Refiner"
    }
  },
  "256": {
    "inputs": {
      "image": "07d2e1d22673808899bba100354351b0d4b5b723a10358c7a9ffe92ec0c98ddc.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "257": {
    "inputs": {
      "image": "56a596334282d0057a0847e7a1f2714e8aa27725718b5a162e3ac33c02e42b17.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "258": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "259": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "260": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "263": {
    "inputs": {
      "model_name": "minimax_h3_latent_upscaler_3d_fp16.safetensors",
      "mode": "scale by multiplier",
      "mode.scale": 2,
      "align": 32,
      "device": "cuda",
      "precision": "fp16",
      "enable_chunking": True,
      "latent": [
        "211",
        0
      ]
    },
    "class_type": "MinimaxH3LatentUpscaler3D",
    "_meta": {
      "title": "Minimax H3 Latent Upscaler (3D)"
    }
  },
  "271": {
    "inputs": {
      "frame_rate": 24,
      "loop_count": 0,
      "filename_prefix": "第二次采样",
      "format": "video/h264-mp4",
      "pix_fmt": "yuv420p",
      "crf": 19,
      "save_metadata": True,
      "trim_to_audio": False,
      "pingpong": False,
      "save_output": True,
      "no_preview": False,
      "images": [
        "219",
        0
      ],
      "audio": [
        "218",
        0
      ]
    },
    "class_type": "VHS_VideoCombine",
    "_meta": {
      "title": "Video Combine 🎥🅥🅗🅢"
    }
  },
  "272": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "273": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "274": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "275": {
    "inputs": {
      "audio": "0ea9bca3948a0baf7983804066a8884203e6452b1c37a109bf6e5dc24e616996.flac",
      "audioUI": ""
    },
    "class_type": "LoadAudio",
    "_meta": {
      "title": "Load Audio"
    }
  }
}

# minimax_h3 7张图片个参考
minimax_h3_7_image_json = {
  "115": {
    "inputs": {
      "aspect_ratio": "16:9 (Widescreen)",
      "megapixels": 0.5,
      "multiple": 32
    },
    "class_type": "ResolutionSelector",
    "_meta": {
      "title": "PASS1 / 16:9 / 0.5MP"
    }
  },
  "119": {
    "inputs": {
      "vae_name": "minimax_h3_video_vae_fp16.safetensors"
    },
    "class_type": "VAELoader",
    "_meta": {
      "title": "Load VAE"
    }
  },
  "120": {
    "inputs": {
      "vae_name": "minimax_h3_audio_vae_fp32.safetensors"
    },
    "class_type": "VAELoader",
    "_meta": {
      "title": "Load VAE"
    }
  },
  "123": {
    "inputs": {
      "sampler_name": "euler"
    },
    "class_type": "KSamplerSelect",
    "_meta": {
      "title": "KSamplerSelect"
    }
  },
  "124": {
    "inputs": {
      "scheduler": "simple",
      "steps": 10,
      "denoise": 1,
      "model": [
        "141",
        0
      ]
    },
    "class_type": "BasicScheduler",
    "_meta": {
      "title": "BasicScheduler"
    }
  },
  "125": {
    "inputs": {
      "noise": [
        "129",
        0
      ],
      "guider": [
        "126",
        0
      ],
      "sampler": [
        "123",
        0
      ],
      "sigmas": [
        "208",
        0
      ],
      "latent_image": [
        "136",
        1
      ]
    },
    "class_type": "SamplerCustomAdvanced",
    "_meta": {
      "title": "SamplerCustomAdvanced"
    }
  },
  "126": {
    "inputs": {
      "model": [
        "141",
        0
      ],
      "conditioning": [
        "136",
        0
      ]
    },
    "class_type": "BasicGuider",
    "_meta": {
      "title": "Basic Guider"
    }
  },
  "127": {
    "inputs": {
      "unet_name": "minimax_h3_hybrid_fl2va_ref2va_b25-49-int8.safetensors",
      "weight_dtype": "default"
    },
    "class_type": "UNETLoader",
    "_meta": {
      "title": "Load Diffusion Model"
    }
  },
  "128": {
    "inputs": {
      "clip_name": "qwen3vl_32b_minimax_h3_int8_convrot.safetensors",
      "type": "minimax",
      "device": "default"
    },
    "class_type": "CLIPLoader",
    "_meta": {
      "title": "Load CLIP"
    }
  },
  "129": {
    "inputs": {
      "noise_seed": 999
    },
    "class_type": "RandomNoise",
    "_meta": {
      "title": "RandomNoise"
    }
  },
  "131": {
    "inputs": {
      "expression": "max(5, round(a * 24)) + (5 - (max(5, round(a * 24)) % 17)) % 17",
      "values.a": [
        "132",
        0
      ]
    },
    "class_type": "ComfyMathExpression",
    "_meta": {
      "title": "Math Expression"
    }
  },
  "132": {
    "inputs": {
      "value": 6
    },
    "class_type": "PrimitiveFloat",
    "_meta": {
      "title": "Float (Duration)"
    }
  },
  "136": {
    "inputs": {
      "prompt": [
        "138",
        0
      ],
      "width": [
        "115",
        0
      ],
      "height": [
        "115",
        1
      ],
      "length": [
        "131",
        1
      ],
      "task_type": "auto",
      "audio_mode": "native",
      "audio_denoise_strength": 1,
      "add_source_as_reference": False,
      "prompt_primary_audio_ordinal": 0,
      "strict_prompt_tags": True,
      "ref_image_size": "match",
      "reference_video_policy": "official_2_to_15s",
      "allow_above_reference_area": True,
      "clip": [
        "128",
        0
      ],
      "video_vae": [
        "119",
        0
      ],
      "audio_vae": [
        "120",
        0
      ],
      "ref_images.ref_image_0": [
        "139",
        0
      ],
      "ref_images.ref_image_1": [
        "256",
        0
      ],
      "ref_images.ref_image_2": [
        "257",
        0
      ],
      "ref_images.ref_image_3": [
        "258",
        0
      ],
      "ref_images.ref_image_4": [
        "259",
        0
      ],
      "ref_images.ref_image_5": [
        "260",
        0
      ],
      "ref_images.ref_image_6": [
        "272",
        0
      ]
    },
    "class_type": "MiniMaxH3AudioConditioningT8",
    "_meta": {
      "title": "T8 条件节点｜通用模式"
    }
  },
  "138": {
    "inputs": {
      "value": "subject_definitions:\\n<Subject 1> is Lin Che from <Picture 1>, a 29-year-old Chinese woman with a chin-length black bob, a small mole at the outer end of her left eyebrow, a dark red buttoned knitted cardigan over a white crew-neck top and black trousers. Preserve her facial identity, natural skin and wardrobe; the three standing views do not dictate her seated performance.\\n<Subject 2> is Chen Li from <Picture 2>, a 48-year-old Chinese man with a square face, short black hair graying at the temples, a slight gap in his right eyebrow, a medium-gray knitted cardigan over a pale blue shirt and dark gray trousers. Preserve his face, age, hair and clothing, not the reference pose.\\n<Subject 3> is the same empty meeting room from <Picture 3>: a matte light-gray rectangular table with its long axis east-west, one chair at each east and west short end, a closed high frosted window in the north wall, a low dark-green six-cubby cabinet against the west wall and a closed brown door in the south wall. Preserve the world-space layout and matte surfaces. Omit the four-view borders, reference viewpoints and incidental objects; the room contains only the two directed people and the one directed recorder.\\n\\nsummary:\\n[reference generation] A 6-second continuous live-action medium shot in <Subject 3>. Lin Che establishes that the recorder is already running and challenges Chen Li to speak on record. The three pictures supply identity and room design, with newly directed framing rather than exact endpoints.\\n\\nretention_analysis:\\n<Subject 1> (appears in [Shot 1]): fully_preserved - Keep Lin Che's identity, bob, dark red cardigan and white inner top while directing the specified seated performance.\\n<Subject 2> (appears in [Shot 1]): fully_preserved - Keep Chen Li's identity, gray temples, gray cardigan and pale blue shirt; the directed seated pose replaces the standing reference.\\n<Subject 3> (appears in [Shot 1]): partially_preserved - Keep the fixed room topology, north-window light, west cabinet and table material; omit multi-view panels and reference framing. The initial camera composition is newly directed.\\n\\ndetailed_description:\\nThe target video is a restrained contemporary Chinese live-action suspense drama, with natural skin texture, readable faces and softly lit matte surfaces.\\n[Shot 1] The camera occupies the open southeast aisle at approximately (1.5,-1.5,1.3) meters relative to the table center and faces northwest toward <Subject 1>. She is seated at the west end on screen-left, torso and head turned east toward <Subject 2>, with her gaze going screen-right. Her chin-length bob, natural eyebrow mark and dark red cardigan remain visible. His gray-clad shoulder and pale blue collar occupy only the extreme right foreground; his body remains at the east seat, and his shoulder does not obscure her face, hands or the recorder. The background shows the west green cabinet and only a geometrically plausible part of the north wall and window. The south door stays behind the camera and out of frame.\\nBoth remain seated on the same two chairs, feet on the floor, with neither changing seats or turning away. <Subject 1>'s two empty hands rest separately on the west table edge; <Subject 2>'s left hand rests on the east edge. There is exactly one small black rectangular audio recorder, about 10 by 3 by 1 centimeters, lying flat on the matte tabletop, long axis east-west and its single red indicator steadily lit. It has no readable display. Its center is 0.35 meters east and 0.12 meters south of the table center. His right fingertips rest on the tabletop three centimeters east of the recorder, separated from its casing. The recorder and both hands remain still until any explicitly directed action.\\nHold the initial pose for about one second. <Subject 1> (S1), using a clear low young-adult female Mandarin voice, measured and direct, says <d>[Chinese] 录音开着。你还要我关掉？</d> The statement about recording is a condition of this conversation, not a command to press a button. Finish speaking by about 4.5 seconds, close the mouth and hold eye contact for the remaining beat. Only speech-related lips, small facial tension and natural breathing change. The listener keeps a closed mouth and still hands. No control is pressed, and the indicator remains steadily red.\\nThe sole key is diffused cool-neutral daylight from the fixed high north window, above seated eye level. It softly illuminates the north-facing cheek, the upper knuckles and the recorder's top plane. Weak, slightly warm bounce from the south wall preserves detail on the shadow side without creating another hard shadow. Hair casts a gentle edge at the jaw, and sleeves retain soft folds. Small contact shadows attach hands and the recorder to the tabletop and extend toward the south in world space; the stationary recorder retains a stationary contact shadow. Keep source positions, exposure and white balance steady. Matte surfaces produce subdued highlights rather than flashes. Changing the viewpoint must not relocate the light to the camera side.\\nUse a 40 mm-equivalent lens at seated eye height, in a medium composition with enough depth of field for the featured face, hands and recorder to remain legible. Focus stays on the featured person's eyes without a focus pull. The camera remains fixed throughout; position, orientation, focal length and framing stay unchanged. The foreground shoulder remains a narrow edge element, not a moving wipe or obstruction. Keep the same single shot from beginning to end.\\nThe output is one full-frame scene, with no reference panels, additional people, automatic captions or decorative overlays. Preserve the settled end pose for the adjacent reverse-angle cut.\\n\\noverall_soundscape:\\nLow steady ventilation and distant, muffled room ambience, with subtle breaths and fabric noise. The stationary recorder produces no playback, beeps or repeated scrape. Keep the room tone unobtrusive beneath the voice.\\n\\nnon_diegetic_music:\\nN/A"
    },
    "class_type": "PrimitiveStringMultiline",
    "_meta": {
      "title": "Input Text (Prompt)"
    }
  },
  "139": {
    "inputs": {
      "image": "2636c786c4c0e6c33db28ba14bbe1c381ed4f7cbd8ae925b745e370640e55fea.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "141": {
    "inputs": {
      "max_resolution": 1024,
      "jpeg_quality": 80,
      "suppress_default_preview": True,
      "preview_frames": [
        "131",
        1
      ],
      "preview_fps": 12,
      "tiny_vae": "taeh3.safetensors",
      "model": [
        "178",
        0
      ]
    },
    "class_type": "ModelPreviewOverrideKJ",
    "_meta": {
      "title": "Model Preview Override KJ"
    }
  },
  "147": {
    "inputs": {
      "lora_name": "minimax_h3_ref2v_turbo_8step_v1.0_768p_comfyui_bf16.safetensors",
      "strength_model": 1.0000000000000002,
      "model": [
        "127",
        0
      ]
    },
    "class_type": "LoraLoaderModelOnly",
    "_meta": {
      "title": "Load LoRA"
    }
  },
  "149": {
    "inputs": {
      "shift_video": 12,
      "shift_audio": 3,
      "model": [
        "147",
        0
      ]
    },
    "class_type": "MiniMaxH3SigmaShift",
    "_meta": {
      "title": "ModelSamplingMiniMaxH3"
    }
  },
  "178": {
    "inputs": {
      "attention": "comfy kitchen attention",
      "model": [
        "149",
        0
      ]
    },
    "class_type": "ModelAttentionBackend",
    "_meta": {
      "title": "ModelAttentionBackend"
    }
  },
  "208": {
    "inputs": {
      "step": 6,
      "sigmas": [
        "254",
        0
      ]
    },
    "class_type": "SplitSigmas",
    "_meta": {
      "title": "SplitSigmas"
    }
  },
  "209": {
    "inputs": {
      "noise": [
        "129",
        0
      ],
      "guider": [
        "126",
        0
      ],
      "sampler": [
        "123",
        0
      ],
      "sigmas": [
        "208",
        1
      ],
      "latent_image": [
        "212",
        0
      ]
    },
    "class_type": "SamplerCustomAdvanced",
    "_meta": {
      "title": "SamplerCustomAdvanced"
    }
  },
  "211": {
    "inputs": {
      "av_latent": [
        "125",
        1
      ]
    },
    "class_type": "LTXVSeparateAVLatent",
    "_meta": {
      "title": "Separate AV Latent"
    }
  },
  "212": {
    "inputs": {
      "video_latent": [
        "263",
        0
      ],
      "audio_latent": [
        "211",
        1
      ]
    },
    "class_type": "LTXVConcatAVLatent",
    "_meta": {
      "title": "Concat AV Latent"
    }
  },
  "218": {
    "inputs": {
      "samples": [
        "209",
        0
      ],
      "vae": [
        "120",
        0
      ]
    },
    "class_type": "VAEDecodeAudio",
    "_meta": {
      "title": "VAE Decode Audio"
    }
  },
  "219": {
    "inputs": {
      "samples": [
        "209",
        0
      ],
      "vae": [
        "119",
        0
      ]
    },
    "class_type": "VAEDecode",
    "_meta": {
      "title": "VAE Decode"
    }
  },
  "254": {
    "inputs": {
      "extra_steps": 1,
      "start_at_sigma": 0.7,
      "end_at_sigma": 0,
      "spacing": "cosine",
      "sigmas": [
        "124",
        0
      ]
    },
    "class_type": "H3SigmaRefiner",
    "_meta": {
      "title": "H3 Sigma Refiner"
    }
  },
  "256": {
    "inputs": {
      "image": "07d2e1d22673808899bba100354351b0d4b5b723a10358c7a9ffe92ec0c98ddc.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "257": {
    "inputs": {
      "image": "56a596334282d0057a0847e7a1f2714e8aa27725718b5a162e3ac33c02e42b17.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "258": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "259": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "260": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "263": {
    "inputs": {
      "model_name": "minimax_h3_latent_upscaler_3d_fp16.safetensors",
      "mode": "scale by multiplier",
      "mode.scale": 2,
      "align": 32,
      "device": "cuda",
      "precision": "fp16",
      "enable_chunking": True,
      "latent": [
        "211",
        0
      ]
    },
    "class_type": "MinimaxH3LatentUpscaler3D",
    "_meta": {
      "title": "Minimax H3 Latent Upscaler (3D)"
    }
  },
  "271": {
    "inputs": {
      "frame_rate": 24,
      "loop_count": 0,
      "filename_prefix": "第二次采样",
      "format": "video/h264-mp4",
      "pix_fmt": "yuv420p",
      "crf": 19,
      "save_metadata": True,
      "trim_to_audio": False,
      "pingpong": False,
      "save_output": True,
      "no_preview": False,
      "images": [
        "219",
        0
      ],
      "audio": [
        "218",
        0
      ]
    },
    "class_type": "VHS_VideoCombine",
    "_meta": {
      "title": "Video Combine 🎥🅥🅗🅢"
    }
  },
  "272": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "273": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "274": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "275": {
    "inputs": {
      "audio": "0ea9bca3948a0baf7983804066a8884203e6452b1c37a109bf6e5dc24e616996.flac",
      "audioUI": ""
    },
    "class_type": "LoadAudio",
    "_meta": {
      "title": "Load Audio"
    }
  }
}

# minimax_h3 6张图片参考
minimax_h3_6_image_json = {
  "115": {
    "inputs": {
      "aspect_ratio": "16:9 (Widescreen)",
      "megapixels": 0.5,
      "multiple": 32
    },
    "class_type": "ResolutionSelector",
    "_meta": {
      "title": "PASS1 / 16:9 / 0.5MP"
    }
  },
  "119": {
    "inputs": {
      "vae_name": "minimax_h3_video_vae_fp16.safetensors"
    },
    "class_type": "VAELoader",
    "_meta": {
      "title": "Load VAE"
    }
  },
  "120": {
    "inputs": {
      "vae_name": "minimax_h3_audio_vae_fp32.safetensors"
    },
    "class_type": "VAELoader",
    "_meta": {
      "title": "Load VAE"
    }
  },
  "123": {
    "inputs": {
      "sampler_name": "euler"
    },
    "class_type": "KSamplerSelect",
    "_meta": {
      "title": "KSamplerSelect"
    }
  },
  "124": {
    "inputs": {
      "scheduler": "simple",
      "steps": 10,
      "denoise": 1,
      "model": [
        "141",
        0
      ]
    },
    "class_type": "BasicScheduler",
    "_meta": {
      "title": "BasicScheduler"
    }
  },
  "125": {
    "inputs": {
      "noise": [
        "129",
        0
      ],
      "guider": [
        "126",
        0
      ],
      "sampler": [
        "123",
        0
      ],
      "sigmas": [
        "208",
        0
      ],
      "latent_image": [
        "136",
        1
      ]
    },
    "class_type": "SamplerCustomAdvanced",
    "_meta": {
      "title": "SamplerCustomAdvanced"
    }
  },
  "126": {
    "inputs": {
      "model": [
        "141",
        0
      ],
      "conditioning": [
        "136",
        0
      ]
    },
    "class_type": "BasicGuider",
    "_meta": {
      "title": "Basic Guider"
    }
  },
  "127": {
    "inputs": {
      "unet_name": "minimax_h3_hybrid_fl2va_ref2va_b25-49-int8.safetensors",
      "weight_dtype": "default"
    },
    "class_type": "UNETLoader",
    "_meta": {
      "title": "Load Diffusion Model"
    }
  },
  "128": {
    "inputs": {
      "clip_name": "qwen3vl_32b_minimax_h3_int8_convrot.safetensors",
      "type": "minimax",
      "device": "default"
    },
    "class_type": "CLIPLoader",
    "_meta": {
      "title": "Load CLIP"
    }
  },
  "129": {
    "inputs": {
      "noise_seed": 999
    },
    "class_type": "RandomNoise",
    "_meta": {
      "title": "RandomNoise"
    }
  },
  "131": {
    "inputs": {
      "expression": "max(5, round(a * 24)) + (5 - (max(5, round(a * 24)) % 17)) % 17",
      "values.a": [
        "132",
        0
      ]
    },
    "class_type": "ComfyMathExpression",
    "_meta": {
      "title": "Math Expression"
    }
  },
  "132": {
    "inputs": {
      "value": 6
    },
    "class_type": "PrimitiveFloat",
    "_meta": {
      "title": "Float (Duration)"
    }
  },
  "136": {
    "inputs": {
      "prompt": [
        "138",
        0
      ],
      "width": [
        "115",
        0
      ],
      "height": [
        "115",
        1
      ],
      "length": [
        "131",
        1
      ],
      "task_type": "auto",
      "audio_mode": "native",
      "audio_denoise_strength": 1,
      "add_source_as_reference": False,
      "prompt_primary_audio_ordinal": 0,
      "strict_prompt_tags": True,
      "ref_image_size": "match",
      "reference_video_policy": "official_2_to_15s",
      "allow_above_reference_area": True,
      "clip": [
        "128",
        0
      ],
      "video_vae": [
        "119",
        0
      ],
      "audio_vae": [
        "120",
        0
      ],
      "ref_images.ref_image_0": [
        "139",
        0
      ],
      "ref_images.ref_image_1": [
        "256",
        0
      ],
      "ref_images.ref_image_2": [
        "257",
        0
      ],
      "ref_images.ref_image_3": [
        "258",
        0
      ],
      "ref_images.ref_image_4": [
        "259",
        0
      ],
      "ref_images.ref_image_5": [
        "260",
        0
      ]
    },
    "class_type": "MiniMaxH3AudioConditioningT8",
    "_meta": {
      "title": "T8 条件节点｜通用模式"
    }
  },
  "138": {
    "inputs": {
      "value": "subject_definitions:\\n<Subject 1> is Lin Che from <Picture 1>, a 29-year-old Chinese woman with a chin-length black bob, a small mole at the outer end of her left eyebrow, a dark red buttoned knitted cardigan over a white crew-neck top and black trousers. Preserve her facial identity, natural skin and wardrobe; the three standing views do not dictate her seated performance.\\n<Subject 2> is Chen Li from <Picture 2>, a 48-year-old Chinese man with a square face, short black hair graying at the temples, a slight gap in his right eyebrow, a medium-gray knitted cardigan over a pale blue shirt and dark gray trousers. Preserve his face, age, hair and clothing, not the reference pose.\\n<Subject 3> is the same empty meeting room from <Picture 3>: a matte light-gray rectangular table with its long axis east-west, one chair at each east and west short end, a closed high frosted window in the north wall, a low dark-green six-cubby cabinet against the west wall and a closed brown door in the south wall. Preserve the world-space layout and matte surfaces. Omit the four-view borders, reference viewpoints and incidental objects; the room contains only the two directed people and the one directed recorder.\\n\\nsummary:\\n[reference generation] A 6-second continuous live-action medium shot in <Subject 3>. Lin Che establishes that the recorder is already running and challenges Chen Li to speak on record. The three pictures supply identity and room design, with newly directed framing rather than exact endpoints.\\n\\nretention_analysis:\\n<Subject 1> (appears in [Shot 1]): fully_preserved - Keep Lin Che's identity, bob, dark red cardigan and white inner top while directing the specified seated performance.\\n<Subject 2> (appears in [Shot 1]): fully_preserved - Keep Chen Li's identity, gray temples, gray cardigan and pale blue shirt; the directed seated pose replaces the standing reference.\\n<Subject 3> (appears in [Shot 1]): partially_preserved - Keep the fixed room topology, north-window light, west cabinet and table material; omit multi-view panels and reference framing. The initial camera composition is newly directed.\\n\\ndetailed_description:\\nThe target video is a restrained contemporary Chinese live-action suspense drama, with natural skin texture, readable faces and softly lit matte surfaces.\\n[Shot 1] The camera occupies the open southeast aisle at approximately (1.5,-1.5,1.3) meters relative to the table center and faces northwest toward <Subject 1>. She is seated at the west end on screen-left, torso and head turned east toward <Subject 2>, with her gaze going screen-right. Her chin-length bob, natural eyebrow mark and dark red cardigan remain visible. His gray-clad shoulder and pale blue collar occupy only the extreme right foreground; his body remains at the east seat, and his shoulder does not obscure her face, hands or the recorder. The background shows the west green cabinet and only a geometrically plausible part of the north wall and window. The south door stays behind the camera and out of frame.\\nBoth remain seated on the same two chairs, feet on the floor, with neither changing seats or turning away. <Subject 1>'s two empty hands rest separately on the west table edge; <Subject 2>'s left hand rests on the east edge. There is exactly one small black rectangular audio recorder, about 10 by 3 by 1 centimeters, lying flat on the matte tabletop, long axis east-west and its single red indicator steadily lit. It has no readable display. Its center is 0.35 meters east and 0.12 meters south of the table center. His right fingertips rest on the tabletop three centimeters east of the recorder, separated from its casing. The recorder and both hands remain still until any explicitly directed action.\\nHold the initial pose for about one second. <Subject 1> (S1), using a clear low young-adult female Mandarin voice, measured and direct, says <d>[Chinese] 录音开着。你还要我关掉？</d> The statement about recording is a condition of this conversation, not a command to press a button. Finish speaking by about 4.5 seconds, close the mouth and hold eye contact for the remaining beat. Only speech-related lips, small facial tension and natural breathing change. The listener keeps a closed mouth and still hands. No control is pressed, and the indicator remains steadily red.\\nThe sole key is diffused cool-neutral daylight from the fixed high north window, above seated eye level. It softly illuminates the north-facing cheek, the upper knuckles and the recorder's top plane. Weak, slightly warm bounce from the south wall preserves detail on the shadow side without creating another hard shadow. Hair casts a gentle edge at the jaw, and sleeves retain soft folds. Small contact shadows attach hands and the recorder to the tabletop and extend toward the south in world space; the stationary recorder retains a stationary contact shadow. Keep source positions, exposure and white balance steady. Matte surfaces produce subdued highlights rather than flashes. Changing the viewpoint must not relocate the light to the camera side.\\nUse a 40 mm-equivalent lens at seated eye height, in a medium composition with enough depth of field for the featured face, hands and recorder to remain legible. Focus stays on the featured person's eyes without a focus pull. The camera remains fixed throughout; position, orientation, focal length and framing stay unchanged. The foreground shoulder remains a narrow edge element, not a moving wipe or obstruction. Keep the same single shot from beginning to end.\\nThe output is one full-frame scene, with no reference panels, additional people, automatic captions or decorative overlays. Preserve the settled end pose for the adjacent reverse-angle cut.\\n\\noverall_soundscape:\\nLow steady ventilation and distant, muffled room ambience, with subtle breaths and fabric noise. The stationary recorder produces no playback, beeps or repeated scrape. Keep the room tone unobtrusive beneath the voice.\\n\\nnon_diegetic_music:\\nN/A"
    },
    "class_type": "PrimitiveStringMultiline",
    "_meta": {
      "title": "Input Text (Prompt)"
    }
  },
  "139": {
    "inputs": {
      "image": "2636c786c4c0e6c33db28ba14bbe1c381ed4f7cbd8ae925b745e370640e55fea.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "141": {
    "inputs": {
      "max_resolution": 1024,
      "jpeg_quality": 80,
      "suppress_default_preview": True,
      "preview_frames": [
        "131",
        1
      ],
      "preview_fps": 12,
      "tiny_vae": "taeh3.safetensors",
      "model": [
        "178",
        0
      ]
    },
    "class_type": "ModelPreviewOverrideKJ",
    "_meta": {
      "title": "Model Preview Override KJ"
    }
  },
  "147": {
    "inputs": {
      "lora_name": "minimax_h3_ref2v_turbo_8step_v1.0_768p_comfyui_bf16.safetensors",
      "strength_model": 1.0000000000000002,
      "model": [
        "127",
        0
      ]
    },
    "class_type": "LoraLoaderModelOnly",
    "_meta": {
      "title": "Load LoRA"
    }
  },
  "149": {
    "inputs": {
      "shift_video": 12,
      "shift_audio": 3,
      "model": [
        "147",
        0
      ]
    },
    "class_type": "MiniMaxH3SigmaShift",
    "_meta": {
      "title": "ModelSamplingMiniMaxH3"
    }
  },
  "178": {
    "inputs": {
      "attention": "comfy kitchen attention",
      "model": [
        "149",
        0
      ]
    },
    "class_type": "ModelAttentionBackend",
    "_meta": {
      "title": "ModelAttentionBackend"
    }
  },
  "208": {
    "inputs": {
      "step": 6,
      "sigmas": [
        "254",
        0
      ]
    },
    "class_type": "SplitSigmas",
    "_meta": {
      "title": "SplitSigmas"
    }
  },
  "209": {
    "inputs": {
      "noise": [
        "129",
        0
      ],
      "guider": [
        "126",
        0
      ],
      "sampler": [
        "123",
        0
      ],
      "sigmas": [
        "208",
        1
      ],
      "latent_image": [
        "212",
        0
      ]
    },
    "class_type": "SamplerCustomAdvanced",
    "_meta": {
      "title": "SamplerCustomAdvanced"
    }
  },
  "211": {
    "inputs": {
      "av_latent": [
        "125",
        1
      ]
    },
    "class_type": "LTXVSeparateAVLatent",
    "_meta": {
      "title": "Separate AV Latent"
    }
  },
  "212": {
    "inputs": {
      "video_latent": [
        "263",
        0
      ],
      "audio_latent": [
        "211",
        1
      ]
    },
    "class_type": "LTXVConcatAVLatent",
    "_meta": {
      "title": "Concat AV Latent"
    }
  },
  "218": {
    "inputs": {
      "samples": [
        "209",
        0
      ],
      "vae": [
        "120",
        0
      ]
    },
    "class_type": "VAEDecodeAudio",
    "_meta": {
      "title": "VAE Decode Audio"
    }
  },
  "219": {
    "inputs": {
      "samples": [
        "209",
        0
      ],
      "vae": [
        "119",
        0
      ]
    },
    "class_type": "VAEDecode",
    "_meta": {
      "title": "VAE Decode"
    }
  },
  "254": {
    "inputs": {
      "extra_steps": 1,
      "start_at_sigma": 0.7,
      "end_at_sigma": 0,
      "spacing": "cosine",
      "sigmas": [
        "124",
        0
      ]
    },
    "class_type": "H3SigmaRefiner",
    "_meta": {
      "title": "H3 Sigma Refiner"
    }
  },
  "256": {
    "inputs": {
      "image": "07d2e1d22673808899bba100354351b0d4b5b723a10358c7a9ffe92ec0c98ddc.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "257": {
    "inputs": {
      "image": "56a596334282d0057a0847e7a1f2714e8aa27725718b5a162e3ac33c02e42b17.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "258": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "259": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "260": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "263": {
    "inputs": {
      "model_name": "minimax_h3_latent_upscaler_3d_fp16.safetensors",
      "mode": "scale by multiplier",
      "mode.scale": 2,
      "align": 32,
      "device": "cuda",
      "precision": "fp16",
      "enable_chunking": True,
      "latent": [
        "211",
        0
      ]
    },
    "class_type": "MinimaxH3LatentUpscaler3D",
    "_meta": {
      "title": "Minimax H3 Latent Upscaler (3D)"
    }
  },
  "271": {
    "inputs": {
      "frame_rate": 24,
      "loop_count": 0,
      "filename_prefix": "第二次采样",
      "format": "video/h264-mp4",
      "pix_fmt": "yuv420p",
      "crf": 19,
      "save_metadata": True,
      "trim_to_audio": False,
      "pingpong": False,
      "save_output": True,
      "no_preview": False,
      "images": [
        "219",
        0
      ],
      "audio": [
        "218",
        0
      ]
    },
    "class_type": "VHS_VideoCombine",
    "_meta": {
      "title": "Video Combine 🎥🅥🅗🅢"
    }
  },
  "272": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "273": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "274": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "275": {
    "inputs": {
      "audio": "0ea9bca3948a0baf7983804066a8884203e6452b1c37a109bf6e5dc24e616996.flac",
      "audioUI": ""
    },
    "class_type": "LoadAudio",
    "_meta": {
      "title": "Load Audio"
    }
  }
}

# minimax_h3 5张图片参考
minimax_h3_5_image_json = {
  "115": {
    "inputs": {
      "aspect_ratio": "16:9 (Widescreen)",
      "megapixels": 0.5,
      "multiple": 32
    },
    "class_type": "ResolutionSelector",
    "_meta": {
      "title": "PASS1 / 16:9 / 0.5MP"
    }
  },
  "119": {
    "inputs": {
      "vae_name": "minimax_h3_video_vae_fp16.safetensors"
    },
    "class_type": "VAELoader",
    "_meta": {
      "title": "Load VAE"
    }
  },
  "120": {
    "inputs": {
      "vae_name": "minimax_h3_audio_vae_fp32.safetensors"
    },
    "class_type": "VAELoader",
    "_meta": {
      "title": "Load VAE"
    }
  },
  "123": {
    "inputs": {
      "sampler_name": "euler"
    },
    "class_type": "KSamplerSelect",
    "_meta": {
      "title": "KSamplerSelect"
    }
  },
  "124": {
    "inputs": {
      "scheduler": "simple",
      "steps": 10,
      "denoise": 1,
      "model": [
        "141",
        0
      ]
    },
    "class_type": "BasicScheduler",
    "_meta": {
      "title": "BasicScheduler"
    }
  },
  "125": {
    "inputs": {
      "noise": [
        "129",
        0
      ],
      "guider": [
        "126",
        0
      ],
      "sampler": [
        "123",
        0
      ],
      "sigmas": [
        "208",
        0
      ],
      "latent_image": [
        "136",
        1
      ]
    },
    "class_type": "SamplerCustomAdvanced",
    "_meta": {
      "title": "SamplerCustomAdvanced"
    }
  },
  "126": {
    "inputs": {
      "model": [
        "141",
        0
      ],
      "conditioning": [
        "136",
        0
      ]
    },
    "class_type": "BasicGuider",
    "_meta": {
      "title": "Basic Guider"
    }
  },
  "127": {
    "inputs": {
      "unet_name": "minimax_h3_hybrid_fl2va_ref2va_b25-49-int8.safetensors",
      "weight_dtype": "default"
    },
    "class_type": "UNETLoader",
    "_meta": {
      "title": "Load Diffusion Model"
    }
  },
  "128": {
    "inputs": {
      "clip_name": "qwen3vl_32b_minimax_h3_int8_convrot.safetensors",
      "type": "minimax",
      "device": "default"
    },
    "class_type": "CLIPLoader",
    "_meta": {
      "title": "Load CLIP"
    }
  },
  "129": {
    "inputs": {
      "noise_seed": 999
    },
    "class_type": "RandomNoise",
    "_meta": {
      "title": "RandomNoise"
    }
  },
  "131": {
    "inputs": {
      "expression": "max(5, round(a * 24)) + (5 - (max(5, round(a * 24)) % 17)) % 17",
      "values.a": [
        "132",
        0
      ]
    },
    "class_type": "ComfyMathExpression",
    "_meta": {
      "title": "Math Expression"
    }
  },
  "132": {
    "inputs": {
      "value": 6
    },
    "class_type": "PrimitiveFloat",
    "_meta": {
      "title": "Float (Duration)"
    }
  },
  "136": {
    "inputs": {
      "prompt": [
        "138",
        0
      ],
      "width": [
        "115",
        0
      ],
      "height": [
        "115",
        1
      ],
      "length": [
        "131",
        1
      ],
      "task_type": "auto",
      "audio_mode": "native",
      "audio_denoise_strength": 1,
      "add_source_as_reference": False,
      "prompt_primary_audio_ordinal": 0,
      "strict_prompt_tags": True,
      "ref_image_size": "match",
      "reference_video_policy": "official_2_to_15s",
      "allow_above_reference_area": True,
      "clip": [
        "128",
        0
      ],
      "video_vae": [
        "119",
        0
      ],
      "audio_vae": [
        "120",
        0
      ],
      "ref_images.ref_image_0": [
        "139",
        0
      ],
      "ref_images.ref_image_1": [
        "256",
        0
      ],
      "ref_images.ref_image_2": [
        "257",
        0
      ],
      "ref_images.ref_image_3": [
        "258",
        0
      ],
      "ref_images.ref_image_4": [
        "259",
        0
      ]
    },
    "class_type": "MiniMaxH3AudioConditioningT8",
    "_meta": {
      "title": "T8 条件节点｜通用模式"
    }
  },
  "138": {
    "inputs": {
      "value": "subject_definitions:\\n<Subject 1> is Lin Che from <Picture 1>, a 29-year-old Chinese woman with a chin-length black bob, a small mole at the outer end of her left eyebrow, a dark red buttoned knitted cardigan over a white crew-neck top and black trousers. Preserve her facial identity, natural skin and wardrobe; the three standing views do not dictate her seated performance.\\n<Subject 2> is Chen Li from <Picture 2>, a 48-year-old Chinese man with a square face, short black hair graying at the temples, a slight gap in his right eyebrow, a medium-gray knitted cardigan over a pale blue shirt and dark gray trousers. Preserve his face, age, hair and clothing, not the reference pose.\\n<Subject 3> is the same empty meeting room from <Picture 3>: a matte light-gray rectangular table with its long axis east-west, one chair at each east and west short end, a closed high frosted window in the north wall, a low dark-green six-cubby cabinet against the west wall and a closed brown door in the south wall. Preserve the world-space layout and matte surfaces. Omit the four-view borders, reference viewpoints and incidental objects; the room contains only the two directed people and the one directed recorder.\\n\\nsummary:\\n[reference generation] A 6-second continuous live-action medium shot in <Subject 3>. Lin Che establishes that the recorder is already running and challenges Chen Li to speak on record. The three pictures supply identity and room design, with newly directed framing rather than exact endpoints.\\n\\nretention_analysis:\\n<Subject 1> (appears in [Shot 1]): fully_preserved - Keep Lin Che's identity, bob, dark red cardigan and white inner top while directing the specified seated performance.\\n<Subject 2> (appears in [Shot 1]): fully_preserved - Keep Chen Li's identity, gray temples, gray cardigan and pale blue shirt; the directed seated pose replaces the standing reference.\\n<Subject 3> (appears in [Shot 1]): partially_preserved - Keep the fixed room topology, north-window light, west cabinet and table material; omit multi-view panels and reference framing. The initial camera composition is newly directed.\\n\\ndetailed_description:\\nThe target video is a restrained contemporary Chinese live-action suspense drama, with natural skin texture, readable faces and softly lit matte surfaces.\\n[Shot 1] The camera occupies the open southeast aisle at approximately (1.5,-1.5,1.3) meters relative to the table center and faces northwest toward <Subject 1>. She is seated at the west end on screen-left, torso and head turned east toward <Subject 2>, with her gaze going screen-right. Her chin-length bob, natural eyebrow mark and dark red cardigan remain visible. His gray-clad shoulder and pale blue collar occupy only the extreme right foreground; his body remains at the east seat, and his shoulder does not obscure her face, hands or the recorder. The background shows the west green cabinet and only a geometrically plausible part of the north wall and window. The south door stays behind the camera and out of frame.\\nBoth remain seated on the same two chairs, feet on the floor, with neither changing seats or turning away. <Subject 1>'s two empty hands rest separately on the west table edge; <Subject 2>'s left hand rests on the east edge. There is exactly one small black rectangular audio recorder, about 10 by 3 by 1 centimeters, lying flat on the matte tabletop, long axis east-west and its single red indicator steadily lit. It has no readable display. Its center is 0.35 meters east and 0.12 meters south of the table center. His right fingertips rest on the tabletop three centimeters east of the recorder, separated from its casing. The recorder and both hands remain still until any explicitly directed action.\\nHold the initial pose for about one second. <Subject 1> (S1), using a clear low young-adult female Mandarin voice, measured and direct, says <d>[Chinese] 录音开着。你还要我关掉？</d> The statement about recording is a condition of this conversation, not a command to press a button. Finish speaking by about 4.5 seconds, close the mouth and hold eye contact for the remaining beat. Only speech-related lips, small facial tension and natural breathing change. The listener keeps a closed mouth and still hands. No control is pressed, and the indicator remains steadily red.\\nThe sole key is diffused cool-neutral daylight from the fixed high north window, above seated eye level. It softly illuminates the north-facing cheek, the upper knuckles and the recorder's top plane. Weak, slightly warm bounce from the south wall preserves detail on the shadow side without creating another hard shadow. Hair casts a gentle edge at the jaw, and sleeves retain soft folds. Small contact shadows attach hands and the recorder to the tabletop and extend toward the south in world space; the stationary recorder retains a stationary contact shadow. Keep source positions, exposure and white balance steady. Matte surfaces produce subdued highlights rather than flashes. Changing the viewpoint must not relocate the light to the camera side.\\nUse a 40 mm-equivalent lens at seated eye height, in a medium composition with enough depth of field for the featured face, hands and recorder to remain legible. Focus stays on the featured person's eyes without a focus pull. The camera remains fixed throughout; position, orientation, focal length and framing stay unchanged. The foreground shoulder remains a narrow edge element, not a moving wipe or obstruction. Keep the same single shot from beginning to end.\\nThe output is one full-frame scene, with no reference panels, additional people, automatic captions or decorative overlays. Preserve the settled end pose for the adjacent reverse-angle cut.\\n\\noverall_soundscape:\\nLow steady ventilation and distant, muffled room ambience, with subtle breaths and fabric noise. The stationary recorder produces no playback, beeps or repeated scrape. Keep the room tone unobtrusive beneath the voice.\\n\\nnon_diegetic_music:\\nN/A"
    },
    "class_type": "PrimitiveStringMultiline",
    "_meta": {
      "title": "Input Text (Prompt)"
    }
  },
  "139": {
    "inputs": {
      "image": "2636c786c4c0e6c33db28ba14bbe1c381ed4f7cbd8ae925b745e370640e55fea.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "141": {
    "inputs": {
      "max_resolution": 1024,
      "jpeg_quality": 80,
      "suppress_default_preview": True,
      "preview_frames": [
        "131",
        1
      ],
      "preview_fps": 12,
      "tiny_vae": "taeh3.safetensors",
      "model": [
        "178",
        0
      ]
    },
    "class_type": "ModelPreviewOverrideKJ",
    "_meta": {
      "title": "Model Preview Override KJ"
    }
  },
  "147": {
    "inputs": {
      "lora_name": "minimax_h3_ref2v_turbo_8step_v1.0_768p_comfyui_bf16.safetensors",
      "strength_model": 1.0000000000000002,
      "model": [
        "127",
        0
      ]
    },
    "class_type": "LoraLoaderModelOnly",
    "_meta": {
      "title": "Load LoRA"
    }
  },
  "149": {
    "inputs": {
      "shift_video": 12,
      "shift_audio": 3,
      "model": [
        "147",
        0
      ]
    },
    "class_type": "MiniMaxH3SigmaShift",
    "_meta": {
      "title": "ModelSamplingMiniMaxH3"
    }
  },
  "178": {
    "inputs": {
      "attention": "comfy kitchen attention",
      "model": [
        "149",
        0
      ]
    },
    "class_type": "ModelAttentionBackend",
    "_meta": {
      "title": "ModelAttentionBackend"
    }
  },
  "208": {
    "inputs": {
      "step": 6,
      "sigmas": [
        "254",
        0
      ]
    },
    "class_type": "SplitSigmas",
    "_meta": {
      "title": "SplitSigmas"
    }
  },
  "209": {
    "inputs": {
      "noise": [
        "129",
        0
      ],
      "guider": [
        "126",
        0
      ],
      "sampler": [
        "123",
        0
      ],
      "sigmas": [
        "208",
        1
      ],
      "latent_image": [
        "212",
        0
      ]
    },
    "class_type": "SamplerCustomAdvanced",
    "_meta": {
      "title": "SamplerCustomAdvanced"
    }
  },
  "211": {
    "inputs": {
      "av_latent": [
        "125",
        1
      ]
    },
    "class_type": "LTXVSeparateAVLatent",
    "_meta": {
      "title": "Separate AV Latent"
    }
  },
  "212": {
    "inputs": {
      "video_latent": [
        "263",
        0
      ],
      "audio_latent": [
        "211",
        1
      ]
    },
    "class_type": "LTXVConcatAVLatent",
    "_meta": {
      "title": "Concat AV Latent"
    }
  },
  "218": {
    "inputs": {
      "samples": [
        "209",
        0
      ],
      "vae": [
        "120",
        0
      ]
    },
    "class_type": "VAEDecodeAudio",
    "_meta": {
      "title": "VAE Decode Audio"
    }
  },
  "219": {
    "inputs": {
      "samples": [
        "209",
        0
      ],
      "vae": [
        "119",
        0
      ]
    },
    "class_type": "VAEDecode",
    "_meta": {
      "title": "VAE Decode"
    }
  },
  "254": {
    "inputs": {
      "extra_steps": 1,
      "start_at_sigma": 0.7,
      "end_at_sigma": 0,
      "spacing": "cosine",
      "sigmas": [
        "124",
        0
      ]
    },
    "class_type": "H3SigmaRefiner",
    "_meta": {
      "title": "H3 Sigma Refiner"
    }
  },
  "256": {
    "inputs": {
      "image": "07d2e1d22673808899bba100354351b0d4b5b723a10358c7a9ffe92ec0c98ddc.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "257": {
    "inputs": {
      "image": "56a596334282d0057a0847e7a1f2714e8aa27725718b5a162e3ac33c02e42b17.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "258": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "259": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "260": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "263": {
    "inputs": {
      "model_name": "minimax_h3_latent_upscaler_3d_fp16.safetensors",
      "mode": "scale by multiplier",
      "mode.scale": 2,
      "align": 32,
      "device": "cuda",
      "precision": "fp16",
      "enable_chunking": True,
      "latent": [
        "211",
        0
      ]
    },
    "class_type": "MinimaxH3LatentUpscaler3D",
    "_meta": {
      "title": "Minimax H3 Latent Upscaler (3D)"
    }
  },
  "271": {
    "inputs": {
      "frame_rate": 24,
      "loop_count": 0,
      "filename_prefix": "第二次采样",
      "format": "video/h264-mp4",
      "pix_fmt": "yuv420p",
      "crf": 19,
      "save_metadata": True,
      "trim_to_audio": False,
      "pingpong": False,
      "save_output": True,
      "no_preview": False,
      "images": [
        "219",
        0
      ],
      "audio": [
        "218",
        0
      ]
    },
    "class_type": "VHS_VideoCombine",
    "_meta": {
      "title": "Video Combine 🎥🅥🅗🅢"
    }
  },
  "272": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "273": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "274": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "275": {
    "inputs": {
      "audio": "0ea9bca3948a0baf7983804066a8884203e6452b1c37a109bf6e5dc24e616996.flac",
      "audioUI": ""
    },
    "class_type": "LoadAudio",
    "_meta": {
      "title": "Load Audio"
    }
  }
}

# minimax_h3 4张图片参考
minimax_h3_4_image_json = {
  "115": {
    "inputs": {
      "aspect_ratio": "16:9 (Widescreen)",
      "megapixels": 0.5,
      "multiple": 32
    },
    "class_type": "ResolutionSelector",
    "_meta": {
      "title": "PASS1 / 16:9 / 0.5MP"
    }
  },
  "119": {
    "inputs": {
      "vae_name": "minimax_h3_video_vae_fp16.safetensors"
    },
    "class_type": "VAELoader",
    "_meta": {
      "title": "Load VAE"
    }
  },
  "120": {
    "inputs": {
      "vae_name": "minimax_h3_audio_vae_fp32.safetensors"
    },
    "class_type": "VAELoader",
    "_meta": {
      "title": "Load VAE"
    }
  },
  "123": {
    "inputs": {
      "sampler_name": "euler"
    },
    "class_type": "KSamplerSelect",
    "_meta": {
      "title": "KSamplerSelect"
    }
  },
  "124": {
    "inputs": {
      "scheduler": "simple",
      "steps": 10,
      "denoise": 1,
      "model": [
        "141",
        0
      ]
    },
    "class_type": "BasicScheduler",
    "_meta": {
      "title": "BasicScheduler"
    }
  },
  "125": {
    "inputs": {
      "noise": [
        "129",
        0
      ],
      "guider": [
        "126",
        0
      ],
      "sampler": [
        "123",
        0
      ],
      "sigmas": [
        "208",
        0
      ],
      "latent_image": [
        "136",
        1
      ]
    },
    "class_type": "SamplerCustomAdvanced",
    "_meta": {
      "title": "SamplerCustomAdvanced"
    }
  },
  "126": {
    "inputs": {
      "model": [
        "141",
        0
      ],
      "conditioning": [
        "136",
        0
      ]
    },
    "class_type": "BasicGuider",
    "_meta": {
      "title": "Basic Guider"
    }
  },
  "127": {
    "inputs": {
      "unet_name": "minimax_h3_hybrid_fl2va_ref2va_b25-49-int8.safetensors",
      "weight_dtype": "default"
    },
    "class_type": "UNETLoader",
    "_meta": {
      "title": "Load Diffusion Model"
    }
  },
  "128": {
    "inputs": {
      "clip_name": "qwen3vl_32b_minimax_h3_int8_convrot.safetensors",
      "type": "minimax",
      "device": "default"
    },
    "class_type": "CLIPLoader",
    "_meta": {
      "title": "Load CLIP"
    }
  },
  "129": {
    "inputs": {
      "noise_seed": 999
    },
    "class_type": "RandomNoise",
    "_meta": {
      "title": "RandomNoise"
    }
  },
  "131": {
    "inputs": {
      "expression": "max(5, round(a * 24)) + (5 - (max(5, round(a * 24)) % 17)) % 17",
      "values.a": [
        "132",
        0
      ]
    },
    "class_type": "ComfyMathExpression",
    "_meta": {
      "title": "Math Expression"
    }
  },
  "132": {
    "inputs": {
      "value": 6
    },
    "class_type": "PrimitiveFloat",
    "_meta": {
      "title": "Float (Duration)"
    }
  },
  "136": {
    "inputs": {
      "prompt": [
        "138",
        0
      ],
      "width": [
        "115",
        0
      ],
      "height": [
        "115",
        1
      ],
      "length": [
        "131",
        1
      ],
      "task_type": "auto",
      "audio_mode": "native",
      "audio_denoise_strength": 1,
      "add_source_as_reference": False,
      "prompt_primary_audio_ordinal": 0,
      "strict_prompt_tags": True,
      "ref_image_size": "match",
      "reference_video_policy": "official_2_to_15s",
      "allow_above_reference_area": True,
      "clip": [
        "128",
        0
      ],
      "video_vae": [
        "119",
        0
      ],
      "audio_vae": [
        "120",
        0
      ],
      "ref_images.ref_image_0": [
        "139",
        0
      ],
      "ref_images.ref_image_1": [
        "256",
        0
      ],
      "ref_images.ref_image_2": [
        "257",
        0
      ],
      "ref_images.ref_image_3": [
        "258",
        0
      ]
    },
    "class_type": "MiniMaxH3AudioConditioningT8",
    "_meta": {
      "title": "T8 条件节点｜通用模式"
    }
  },
  "138": {
    "inputs": {
      "value": "subject_definitions:\\n<Subject 1> is Lin Che from <Picture 1>, a 29-year-old Chinese woman with a chin-length black bob, a small mole at the outer end of her left eyebrow, a dark red buttoned knitted cardigan over a white crew-neck top and black trousers. Preserve her facial identity, natural skin and wardrobe; the three standing views do not dictate her seated performance.\\n<Subject 2> is Chen Li from <Picture 2>, a 48-year-old Chinese man with a square face, short black hair graying at the temples, a slight gap in his right eyebrow, a medium-gray knitted cardigan over a pale blue shirt and dark gray trousers. Preserve his face, age, hair and clothing, not the reference pose.\\n<Subject 3> is the same empty meeting room from <Picture 3>: a matte light-gray rectangular table with its long axis east-west, one chair at each east and west short end, a closed high frosted window in the north wall, a low dark-green six-cubby cabinet against the west wall and a closed brown door in the south wall. Preserve the world-space layout and matte surfaces. Omit the four-view borders, reference viewpoints and incidental objects; the room contains only the two directed people and the one directed recorder.\\n\\nsummary:\\n[reference generation] A 6-second continuous live-action medium shot in <Subject 3>. Lin Che establishes that the recorder is already running and challenges Chen Li to speak on record. The three pictures supply identity and room design, with newly directed framing rather than exact endpoints.\\n\\nretention_analysis:\\n<Subject 1> (appears in [Shot 1]): fully_preserved - Keep Lin Che's identity, bob, dark red cardigan and white inner top while directing the specified seated performance.\\n<Subject 2> (appears in [Shot 1]): fully_preserved - Keep Chen Li's identity, gray temples, gray cardigan and pale blue shirt; the directed seated pose replaces the standing reference.\\n<Subject 3> (appears in [Shot 1]): partially_preserved - Keep the fixed room topology, north-window light, west cabinet and table material; omit multi-view panels and reference framing. The initial camera composition is newly directed.\\n\\ndetailed_description:\\nThe target video is a restrained contemporary Chinese live-action suspense drama, with natural skin texture, readable faces and softly lit matte surfaces.\\n[Shot 1] The camera occupies the open southeast aisle at approximately (1.5,-1.5,1.3) meters relative to the table center and faces northwest toward <Subject 1>. She is seated at the west end on screen-left, torso and head turned east toward <Subject 2>, with her gaze going screen-right. Her chin-length bob, natural eyebrow mark and dark red cardigan remain visible. His gray-clad shoulder and pale blue collar occupy only the extreme right foreground; his body remains at the east seat, and his shoulder does not obscure her face, hands or the recorder. The background shows the west green cabinet and only a geometrically plausible part of the north wall and window. The south door stays behind the camera and out of frame.\\nBoth remain seated on the same two chairs, feet on the floor, with neither changing seats or turning away. <Subject 1>'s two empty hands rest separately on the west table edge; <Subject 2>'s left hand rests on the east edge. There is exactly one small black rectangular audio recorder, about 10 by 3 by 1 centimeters, lying flat on the matte tabletop, long axis east-west and its single red indicator steadily lit. It has no readable display. Its center is 0.35 meters east and 0.12 meters south of the table center. His right fingertips rest on the tabletop three centimeters east of the recorder, separated from its casing. The recorder and both hands remain still until any explicitly directed action.\\nHold the initial pose for about one second. <Subject 1> (S1), using a clear low young-adult female Mandarin voice, measured and direct, says <d>[Chinese] 录音开着。你还要我关掉？</d> The statement about recording is a condition of this conversation, not a command to press a button. Finish speaking by about 4.5 seconds, close the mouth and hold eye contact for the remaining beat. Only speech-related lips, small facial tension and natural breathing change. The listener keeps a closed mouth and still hands. No control is pressed, and the indicator remains steadily red.\\nThe sole key is diffused cool-neutral daylight from the fixed high north window, above seated eye level. It softly illuminates the north-facing cheek, the upper knuckles and the recorder's top plane. Weak, slightly warm bounce from the south wall preserves detail on the shadow side without creating another hard shadow. Hair casts a gentle edge at the jaw, and sleeves retain soft folds. Small contact shadows attach hands and the recorder to the tabletop and extend toward the south in world space; the stationary recorder retains a stationary contact shadow. Keep source positions, exposure and white balance steady. Matte surfaces produce subdued highlights rather than flashes. Changing the viewpoint must not relocate the light to the camera side.\\nUse a 40 mm-equivalent lens at seated eye height, in a medium composition with enough depth of field for the featured face, hands and recorder to remain legible. Focus stays on the featured person's eyes without a focus pull. The camera remains fixed throughout; position, orientation, focal length and framing stay unchanged. The foreground shoulder remains a narrow edge element, not a moving wipe or obstruction. Keep the same single shot from beginning to end.\\nThe output is one full-frame scene, with no reference panels, additional people, automatic captions or decorative overlays. Preserve the settled end pose for the adjacent reverse-angle cut.\\n\\noverall_soundscape:\\nLow steady ventilation and distant, muffled room ambience, with subtle breaths and fabric noise. The stationary recorder produces no playback, beeps or repeated scrape. Keep the room tone unobtrusive beneath the voice.\\n\\nnon_diegetic_music:\\nN/A"
    },
    "class_type": "PrimitiveStringMultiline",
    "_meta": {
      "title": "Input Text (Prompt)"
    }
  },
  "139": {
    "inputs": {
      "image": "2636c786c4c0e6c33db28ba14bbe1c381ed4f7cbd8ae925b745e370640e55fea.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "141": {
    "inputs": {
      "max_resolution": 1024,
      "jpeg_quality": 80,
      "suppress_default_preview": True,
      "preview_frames": [
        "131",
        1
      ],
      "preview_fps": 12,
      "tiny_vae": "taeh3.safetensors",
      "model": [
        "178",
        0
      ]
    },
    "class_type": "ModelPreviewOverrideKJ",
    "_meta": {
      "title": "Model Preview Override KJ"
    }
  },
  "147": {
    "inputs": {
      "lora_name": "minimax_h3_ref2v_turbo_8step_v1.0_768p_comfyui_bf16.safetensors",
      "strength_model": 1.0000000000000002,
      "model": [
        "127",
        0
      ]
    },
    "class_type": "LoraLoaderModelOnly",
    "_meta": {
      "title": "Load LoRA"
    }
  },
  "149": {
    "inputs": {
      "shift_video": 12,
      "shift_audio": 3,
      "model": [
        "147",
        0
      ]
    },
    "class_type": "MiniMaxH3SigmaShift",
    "_meta": {
      "title": "ModelSamplingMiniMaxH3"
    }
  },
  "178": {
    "inputs": {
      "attention": "comfy kitchen attention",
      "model": [
        "149",
        0
      ]
    },
    "class_type": "ModelAttentionBackend",
    "_meta": {
      "title": "ModelAttentionBackend"
    }
  },
  "208": {
    "inputs": {
      "step": 6,
      "sigmas": [
        "254",
        0
      ]
    },
    "class_type": "SplitSigmas",
    "_meta": {
      "title": "SplitSigmas"
    }
  },
  "209": {
    "inputs": {
      "noise": [
        "129",
        0
      ],
      "guider": [
        "126",
        0
      ],
      "sampler": [
        "123",
        0
      ],
      "sigmas": [
        "208",
        1
      ],
      "latent_image": [
        "212",
        0
      ]
    },
    "class_type": "SamplerCustomAdvanced",
    "_meta": {
      "title": "SamplerCustomAdvanced"
    }
  },
  "211": {
    "inputs": {
      "av_latent": [
        "125",
        1
      ]
    },
    "class_type": "LTXVSeparateAVLatent",
    "_meta": {
      "title": "Separate AV Latent"
    }
  },
  "212": {
    "inputs": {
      "video_latent": [
        "263",
        0
      ],
      "audio_latent": [
        "211",
        1
      ]
    },
    "class_type": "LTXVConcatAVLatent",
    "_meta": {
      "title": "Concat AV Latent"
    }
  },
  "218": {
    "inputs": {
      "samples": [
        "209",
        0
      ],
      "vae": [
        "120",
        0
      ]
    },
    "class_type": "VAEDecodeAudio",
    "_meta": {
      "title": "VAE Decode Audio"
    }
  },
  "219": {
    "inputs": {
      "samples": [
        "209",
        0
      ],
      "vae": [
        "119",
        0
      ]
    },
    "class_type": "VAEDecode",
    "_meta": {
      "title": "VAE Decode"
    }
  },
  "254": {
    "inputs": {
      "extra_steps": 1,
      "start_at_sigma": 0.7,
      "end_at_sigma": 0,
      "spacing": "cosine",
      "sigmas": [
        "124",
        0
      ]
    },
    "class_type": "H3SigmaRefiner",
    "_meta": {
      "title": "H3 Sigma Refiner"
    }
  },
  "256": {
    "inputs": {
      "image": "07d2e1d22673808899bba100354351b0d4b5b723a10358c7a9ffe92ec0c98ddc.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "257": {
    "inputs": {
      "image": "56a596334282d0057a0847e7a1f2714e8aa27725718b5a162e3ac33c02e42b17.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "258": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "259": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "260": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "263": {
    "inputs": {
      "model_name": "minimax_h3_latent_upscaler_3d_fp16.safetensors",
      "mode": "scale by multiplier",
      "mode.scale": 2,
      "align": 32,
      "device": "cuda",
      "precision": "fp16",
      "enable_chunking": True,
      "latent": [
        "211",
        0
      ]
    },
    "class_type": "MinimaxH3LatentUpscaler3D",
    "_meta": {
      "title": "Minimax H3 Latent Upscaler (3D)"
    }
  },
  "271": {
    "inputs": {
      "frame_rate": 24,
      "loop_count": 0,
      "filename_prefix": "第二次采样",
      "format": "video/h264-mp4",
      "pix_fmt": "yuv420p",
      "crf": 19,
      "save_metadata": True,
      "trim_to_audio": False,
      "pingpong": False,
      "save_output": True,
      "no_preview": False,
      "images": [
        "219",
        0
      ],
      "audio": [
        "218",
        0
      ]
    },
    "class_type": "VHS_VideoCombine",
    "_meta": {
      "title": "Video Combine 🎥🅥🅗🅢"
    }
  },
  "272": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "273": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "274": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "275": {
    "inputs": {
      "audio": "0ea9bca3948a0baf7983804066a8884203e6452b1c37a109bf6e5dc24e616996.flac",
      "audioUI": ""
    },
    "class_type": "LoadAudio",
    "_meta": {
      "title": "Load Audio"
    }
  }
}

# minimax_h3 3张图片参考
minimax_h3_3_image_json = {
  "115": {
    "inputs": {
      "aspect_ratio": "16:9 (Widescreen)",
      "megapixels": 0.5,
      "multiple": 32
    },
    "class_type": "ResolutionSelector",
    "_meta": {
      "title": "PASS1 / 16:9 / 0.5MP"
    }
  },
  "119": {
    "inputs": {
      "vae_name": "minimax_h3_video_vae_fp16.safetensors"
    },
    "class_type": "VAELoader",
    "_meta": {
      "title": "Load VAE"
    }
  },
  "120": {
    "inputs": {
      "vae_name": "minimax_h3_audio_vae_fp32.safetensors"
    },
    "class_type": "VAELoader",
    "_meta": {
      "title": "Load VAE"
    }
  },
  "123": {
    "inputs": {
      "sampler_name": "euler"
    },
    "class_type": "KSamplerSelect",
    "_meta": {
      "title": "KSamplerSelect"
    }
  },
  "124": {
    "inputs": {
      "scheduler": "simple",
      "steps": 10,
      "denoise": 1,
      "model": [
        "141",
        0
      ]
    },
    "class_type": "BasicScheduler",
    "_meta": {
      "title": "BasicScheduler"
    }
  },
  "125": {
    "inputs": {
      "noise": [
        "129",
        0
      ],
      "guider": [
        "126",
        0
      ],
      "sampler": [
        "123",
        0
      ],
      "sigmas": [
        "208",
        0
      ],
      "latent_image": [
        "136",
        1
      ]
    },
    "class_type": "SamplerCustomAdvanced",
    "_meta": {
      "title": "SamplerCustomAdvanced"
    }
  },
  "126": {
    "inputs": {
      "model": [
        "141",
        0
      ],
      "conditioning": [
        "136",
        0
      ]
    },
    "class_type": "BasicGuider",
    "_meta": {
      "title": "Basic Guider"
    }
  },
  "127": {
    "inputs": {
      "unet_name": "minimax_h3_hybrid_fl2va_ref2va_b25-49-int8.safetensors",
      "weight_dtype": "default"
    },
    "class_type": "UNETLoader",
    "_meta": {
      "title": "Load Diffusion Model"
    }
  },
  "128": {
    "inputs": {
      "clip_name": "qwen3vl_32b_minimax_h3_int8_convrot.safetensors",
      "type": "minimax",
      "device": "default"
    },
    "class_type": "CLIPLoader",
    "_meta": {
      "title": "Load CLIP"
    }
  },
  "129": {
    "inputs": {
      "noise_seed": 999
    },
    "class_type": "RandomNoise",
    "_meta": {
      "title": "RandomNoise"
    }
  },
  "131": {
    "inputs": {
      "expression": "max(5, round(a * 24)) + (5 - (max(5, round(a * 24)) % 17)) % 17",
      "values.a": [
        "132",
        0
      ]
    },
    "class_type": "ComfyMathExpression",
    "_meta": {
      "title": "Math Expression"
    }
  },
  "132": {
    "inputs": {
      "value": 6
    },
    "class_type": "PrimitiveFloat",
    "_meta": {
      "title": "Float (Duration)"
    }
  },
  "136": {
    "inputs": {
      "prompt": [
        "138",
        0
      ],
      "width": [
        "115",
        0
      ],
      "height": [
        "115",
        1
      ],
      "length": [
        "131",
        1
      ],
      "task_type": "auto",
      "audio_mode": "native",
      "audio_denoise_strength": 1,
      "add_source_as_reference": False,
      "prompt_primary_audio_ordinal": 0,
      "strict_prompt_tags": True,
      "ref_image_size": "match",
      "reference_video_policy": "official_2_to_15s",
      "allow_above_reference_area": True,
      "clip": [
        "128",
        0
      ],
      "video_vae": [
        "119",
        0
      ],
      "audio_vae": [
        "120",
        0
      ],
      "ref_images.ref_image_0": [
        "139",
        0
      ],
      "ref_images.ref_image_1": [
        "256",
        0
      ],
      "ref_images.ref_image_2": [
        "257",
        0
      ]
    },
    "class_type": "MiniMaxH3AudioConditioningT8",
    "_meta": {
      "title": "T8 条件节点｜通用模式"
    }
  },
  "138": {
    "inputs": {
      "value": "subject_definitions:\\n<Subject 1> is Lin Che from <Picture 1>, a 29-year-old Chinese woman with a chin-length black bob, a small mole at the outer end of her left eyebrow, a dark red buttoned knitted cardigan over a white crew-neck top and black trousers. Preserve her facial identity, natural skin and wardrobe; the three standing views do not dictate her seated performance.\\n<Subject 2> is Chen Li from <Picture 2>, a 48-year-old Chinese man with a square face, short black hair graying at the temples, a slight gap in his right eyebrow, a medium-gray knitted cardigan over a pale blue shirt and dark gray trousers. Preserve his face, age, hair and clothing, not the reference pose.\\n<Subject 3> is the same empty meeting room from <Picture 3>: a matte light-gray rectangular table with its long axis east-west, one chair at each east and west short end, a closed high frosted window in the north wall, a low dark-green six-cubby cabinet against the west wall and a closed brown door in the south wall. Preserve the world-space layout and matte surfaces. Omit the four-view borders, reference viewpoints and incidental objects; the room contains only the two directed people and the one directed recorder.\\n\\nsummary:\\n[reference generation] A 6-second continuous live-action medium shot in <Subject 3>. Lin Che establishes that the recorder is already running and challenges Chen Li to speak on record. The three pictures supply identity and room design, with newly directed framing rather than exact endpoints.\\n\\nretention_analysis:\\n<Subject 1> (appears in [Shot 1]): fully_preserved - Keep Lin Che's identity, bob, dark red cardigan and white inner top while directing the specified seated performance.\\n<Subject 2> (appears in [Shot 1]): fully_preserved - Keep Chen Li's identity, gray temples, gray cardigan and pale blue shirt; the directed seated pose replaces the standing reference.\\n<Subject 3> (appears in [Shot 1]): partially_preserved - Keep the fixed room topology, north-window light, west cabinet and table material; omit multi-view panels and reference framing. The initial camera composition is newly directed.\\n\\ndetailed_description:\\nThe target video is a restrained contemporary Chinese live-action suspense drama, with natural skin texture, readable faces and softly lit matte surfaces.\\n[Shot 1] The camera occupies the open southeast aisle at approximately (1.5,-1.5,1.3) meters relative to the table center and faces northwest toward <Subject 1>. She is seated at the west end on screen-left, torso and head turned east toward <Subject 2>, with her gaze going screen-right. Her chin-length bob, natural eyebrow mark and dark red cardigan remain visible. His gray-clad shoulder and pale blue collar occupy only the extreme right foreground; his body remains at the east seat, and his shoulder does not obscure her face, hands or the recorder. The background shows the west green cabinet and only a geometrically plausible part of the north wall and window. The south door stays behind the camera and out of frame.\\nBoth remain seated on the same two chairs, feet on the floor, with neither changing seats or turning away. <Subject 1>'s two empty hands rest separately on the west table edge; <Subject 2>'s left hand rests on the east edge. There is exactly one small black rectangular audio recorder, about 10 by 3 by 1 centimeters, lying flat on the matte tabletop, long axis east-west and its single red indicator steadily lit. It has no readable display. Its center is 0.35 meters east and 0.12 meters south of the table center. His right fingertips rest on the tabletop three centimeters east of the recorder, separated from its casing. The recorder and both hands remain still until any explicitly directed action.\\nHold the initial pose for about one second. <Subject 1> (S1), using a clear low young-adult female Mandarin voice, measured and direct, says <d>[Chinese] 录音开着。你还要我关掉？</d> The statement about recording is a condition of this conversation, not a command to press a button. Finish speaking by about 4.5 seconds, close the mouth and hold eye contact for the remaining beat. Only speech-related lips, small facial tension and natural breathing change. The listener keeps a closed mouth and still hands. No control is pressed, and the indicator remains steadily red.\\nThe sole key is diffused cool-neutral daylight from the fixed high north window, above seated eye level. It softly illuminates the north-facing cheek, the upper knuckles and the recorder's top plane. Weak, slightly warm bounce from the south wall preserves detail on the shadow side without creating another hard shadow. Hair casts a gentle edge at the jaw, and sleeves retain soft folds. Small contact shadows attach hands and the recorder to the tabletop and extend toward the south in world space; the stationary recorder retains a stationary contact shadow. Keep source positions, exposure and white balance steady. Matte surfaces produce subdued highlights rather than flashes. Changing the viewpoint must not relocate the light to the camera side.\\nUse a 40 mm-equivalent lens at seated eye height, in a medium composition with enough depth of field for the featured face, hands and recorder to remain legible. Focus stays on the featured person's eyes without a focus pull. The camera remains fixed throughout; position, orientation, focal length and framing stay unchanged. The foreground shoulder remains a narrow edge element, not a moving wipe or obstruction. Keep the same single shot from beginning to end.\\nThe output is one full-frame scene, with no reference panels, additional people, automatic captions or decorative overlays. Preserve the settled end pose for the adjacent reverse-angle cut.\\n\\noverall_soundscape:\\nLow steady ventilation and distant, muffled room ambience, with subtle breaths and fabric noise. The stationary recorder produces no playback, beeps or repeated scrape. Keep the room tone unobtrusive beneath the voice.\\n\\nnon_diegetic_music:\\nN/A"
    },
    "class_type": "PrimitiveStringMultiline",
    "_meta": {
      "title": "Input Text (Prompt)"
    }
  },
  "139": {
    "inputs": {
      "image": "2636c786c4c0e6c33db28ba14bbe1c381ed4f7cbd8ae925b745e370640e55fea.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "141": {
    "inputs": {
      "max_resolution": 1024,
      "jpeg_quality": 80,
      "suppress_default_preview": True,
      "preview_frames": [
        "131",
        1
      ],
      "preview_fps": 12,
      "tiny_vae": "taeh3.safetensors",
      "model": [
        "178",
        0
      ]
    },
    "class_type": "ModelPreviewOverrideKJ",
    "_meta": {
      "title": "Model Preview Override KJ"
    }
  },
  "147": {
    "inputs": {
      "lora_name": "minimax_h3_ref2v_turbo_8step_v1.0_768p_comfyui_bf16.safetensors",
      "strength_model": 1.0000000000000002,
      "model": [
        "127",
        0
      ]
    },
    "class_type": "LoraLoaderModelOnly",
    "_meta": {
      "title": "Load LoRA"
    }
  },
  "149": {
    "inputs": {
      "shift_video": 12,
      "shift_audio": 3,
      "model": [
        "147",
        0
      ]
    },
    "class_type": "MiniMaxH3SigmaShift",
    "_meta": {
      "title": "ModelSamplingMiniMaxH3"
    }
  },
  "178": {
    "inputs": {
      "attention": "comfy kitchen attention",
      "model": [
        "149",
        0
      ]
    },
    "class_type": "ModelAttentionBackend",
    "_meta": {
      "title": "ModelAttentionBackend"
    }
  },
  "208": {
    "inputs": {
      "step": 6,
      "sigmas": [
        "254",
        0
      ]
    },
    "class_type": "SplitSigmas",
    "_meta": {
      "title": "SplitSigmas"
    }
  },
  "209": {
    "inputs": {
      "noise": [
        "129",
        0
      ],
      "guider": [
        "126",
        0
      ],
      "sampler": [
        "123",
        0
      ],
      "sigmas": [
        "208",
        1
      ],
      "latent_image": [
        "212",
        0
      ]
    },
    "class_type": "SamplerCustomAdvanced",
    "_meta": {
      "title": "SamplerCustomAdvanced"
    }
  },
  "211": {
    "inputs": {
      "av_latent": [
        "125",
        1
      ]
    },
    "class_type": "LTXVSeparateAVLatent",
    "_meta": {
      "title": "Separate AV Latent"
    }
  },
  "212": {
    "inputs": {
      "video_latent": [
        "263",
        0
      ],
      "audio_latent": [
        "211",
        1
      ]
    },
    "class_type": "LTXVConcatAVLatent",
    "_meta": {
      "title": "Concat AV Latent"
    }
  },
  "218": {
    "inputs": {
      "samples": [
        "209",
        0
      ],
      "vae": [
        "120",
        0
      ]
    },
    "class_type": "VAEDecodeAudio",
    "_meta": {
      "title": "VAE Decode Audio"
    }
  },
  "219": {
    "inputs": {
      "samples": [
        "209",
        0
      ],
      "vae": [
        "119",
        0
      ]
    },
    "class_type": "VAEDecode",
    "_meta": {
      "title": "VAE Decode"
    }
  },
  "254": {
    "inputs": {
      "extra_steps": 1,
      "start_at_sigma": 0.7,
      "end_at_sigma": 0,
      "spacing": "cosine",
      "sigmas": [
        "124",
        0
      ]
    },
    "class_type": "H3SigmaRefiner",
    "_meta": {
      "title": "H3 Sigma Refiner"
    }
  },
  "256": {
    "inputs": {
      "image": "07d2e1d22673808899bba100354351b0d4b5b723a10358c7a9ffe92ec0c98ddc.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "257": {
    "inputs": {
      "image": "56a596334282d0057a0847e7a1f2714e8aa27725718b5a162e3ac33c02e42b17.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "258": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "259": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "260": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "263": {
    "inputs": {
      "model_name": "minimax_h3_latent_upscaler_3d_fp16.safetensors",
      "mode": "scale by multiplier",
      "mode.scale": 2,
      "align": 32,
      "device": "cuda",
      "precision": "fp16",
      "enable_chunking": True,
      "latent": [
        "211",
        0
      ]
    },
    "class_type": "MinimaxH3LatentUpscaler3D",
    "_meta": {
      "title": "Minimax H3 Latent Upscaler (3D)"
    }
  },
  "271": {
    "inputs": {
      "frame_rate": 24,
      "loop_count": 0,
      "filename_prefix": "第二次采样",
      "format": "video/h264-mp4",
      "pix_fmt": "yuv420p",
      "crf": 19,
      "save_metadata": True,
      "trim_to_audio": False,
      "pingpong": False,
      "save_output": True,
      "no_preview": False,
      "images": [
        "219",
        0
      ],
      "audio": [
        "218",
        0
      ]
    },
    "class_type": "VHS_VideoCombine",
    "_meta": {
      "title": "Video Combine 🎥🅥🅗🅢"
    }
  },
  "272": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "273": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "274": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "275": {
    "inputs": {
      "audio": "0ea9bca3948a0baf7983804066a8884203e6452b1c37a109bf6e5dc24e616996.flac",
      "audioUI": ""
    },
    "class_type": "LoadAudio",
    "_meta": {
      "title": "Load Audio"
    }
  }
}

# minimax_h3 2张图片参考
minimax_h3_2_image_json = {
  "115": {
    "inputs": {
      "aspect_ratio": "16:9 (Widescreen)",
      "megapixels": 0.5,
      "multiple": 32
    },
    "class_type": "ResolutionSelector",
    "_meta": {
      "title": "PASS1 / 16:9 / 0.5MP"
    }
  },
  "119": {
    "inputs": {
      "vae_name": "minimax_h3_video_vae_fp16.safetensors"
    },
    "class_type": "VAELoader",
    "_meta": {
      "title": "Load VAE"
    }
  },
  "120": {
    "inputs": {
      "vae_name": "minimax_h3_audio_vae_fp32.safetensors"
    },
    "class_type": "VAELoader",
    "_meta": {
      "title": "Load VAE"
    }
  },
  "123": {
    "inputs": {
      "sampler_name": "euler"
    },
    "class_type": "KSamplerSelect",
    "_meta": {
      "title": "KSamplerSelect"
    }
  },
  "124": {
    "inputs": {
      "scheduler": "simple",
      "steps": 10,
      "denoise": 1,
      "model": [
        "141",
        0
      ]
    },
    "class_type": "BasicScheduler",
    "_meta": {
      "title": "BasicScheduler"
    }
  },
  "125": {
    "inputs": {
      "noise": [
        "129",
        0
      ],
      "guider": [
        "126",
        0
      ],
      "sampler": [
        "123",
        0
      ],
      "sigmas": [
        "208",
        0
      ],
      "latent_image": [
        "136",
        1
      ]
    },
    "class_type": "SamplerCustomAdvanced",
    "_meta": {
      "title": "SamplerCustomAdvanced"
    }
  },
  "126": {
    "inputs": {
      "model": [
        "141",
        0
      ],
      "conditioning": [
        "136",
        0
      ]
    },
    "class_type": "BasicGuider",
    "_meta": {
      "title": "Basic Guider"
    }
  },
  "127": {
    "inputs": {
      "unet_name": "minimax_h3_hybrid_fl2va_ref2va_b25-49-int8.safetensors",
      "weight_dtype": "default"
    },
    "class_type": "UNETLoader",
    "_meta": {
      "title": "Load Diffusion Model"
    }
  },
  "128": {
    "inputs": {
      "clip_name": "qwen3vl_32b_minimax_h3_int8_convrot.safetensors",
      "type": "minimax",
      "device": "default"
    },
    "class_type": "CLIPLoader",
    "_meta": {
      "title": "Load CLIP"
    }
  },
  "129": {
    "inputs": {
      "noise_seed": 999
    },
    "class_type": "RandomNoise",
    "_meta": {
      "title": "RandomNoise"
    }
  },
  "131": {
    "inputs": {
      "expression": "max(5, round(a * 24)) + (5 - (max(5, round(a * 24)) % 17)) % 17",
      "values.a": [
        "132",
        0
      ]
    },
    "class_type": "ComfyMathExpression",
    "_meta": {
      "title": "Math Expression"
    }
  },
  "132": {
    "inputs": {
      "value": 6
    },
    "class_type": "PrimitiveFloat",
    "_meta": {
      "title": "Float (Duration)"
    }
  },
  "136": {
    "inputs": {
      "prompt": [
        "138",
        0
      ],
      "width": [
        "115",
        0
      ],
      "height": [
        "115",
        1
      ],
      "length": [
        "131",
        1
      ],
      "task_type": "auto",
      "audio_mode": "native",
      "audio_denoise_strength": 1,
      "add_source_as_reference": False,
      "prompt_primary_audio_ordinal": 0,
      "strict_prompt_tags": True,
      "ref_image_size": "match",
      "reference_video_policy": "official_2_to_15s",
      "allow_above_reference_area": True,
      "clip": [
        "128",
        0
      ],
      "video_vae": [
        "119",
        0
      ],
      "audio_vae": [
        "120",
        0
      ],
      "ref_images.ref_image_0": [
        "139",
        0
      ],
      "ref_images.ref_image_1": [
        "256",
        0
      ]
    },
    "class_type": "MiniMaxH3AudioConditioningT8",
    "_meta": {
      "title": "T8 条件节点｜通用模式"
    }
  },
  "138": {
    "inputs": {
      "value": "subject_definitions:\\n<Subject 1> is Lin Che from <Picture 1>, a 29-year-old Chinese woman with a chin-length black bob, a small mole at the outer end of her left eyebrow, a dark red buttoned knitted cardigan over a white crew-neck top and black trousers. Preserve her facial identity, natural skin and wardrobe; the three standing views do not dictate her seated performance.\\n<Subject 2> is Chen Li from <Picture 2>, a 48-year-old Chinese man with a square face, short black hair graying at the temples, a slight gap in his right eyebrow, a medium-gray knitted cardigan over a pale blue shirt and dark gray trousers. Preserve his face, age, hair and clothing, not the reference pose.\\n<Subject 3> is the same empty meeting room from <Picture 3>: a matte light-gray rectangular table with its long axis east-west, one chair at each east and west short end, a closed high frosted window in the north wall, a low dark-green six-cubby cabinet against the west wall and a closed brown door in the south wall. Preserve the world-space layout and matte surfaces. Omit the four-view borders, reference viewpoints and incidental objects; the room contains only the two directed people and the one directed recorder.\\n\\nsummary:\\n[reference generation] A 6-second continuous live-action medium shot in <Subject 3>. Lin Che establishes that the recorder is already running and challenges Chen Li to speak on record. The three pictures supply identity and room design, with newly directed framing rather than exact endpoints.\\n\\nretention_analysis:\\n<Subject 1> (appears in [Shot 1]): fully_preserved - Keep Lin Che's identity, bob, dark red cardigan and white inner top while directing the specified seated performance.\\n<Subject 2> (appears in [Shot 1]): fully_preserved - Keep Chen Li's identity, gray temples, gray cardigan and pale blue shirt; the directed seated pose replaces the standing reference.\\n<Subject 3> (appears in [Shot 1]): partially_preserved - Keep the fixed room topology, north-window light, west cabinet and table material; omit multi-view panels and reference framing. The initial camera composition is newly directed.\\n\\ndetailed_description:\\nThe target video is a restrained contemporary Chinese live-action suspense drama, with natural skin texture, readable faces and softly lit matte surfaces.\\n[Shot 1] The camera occupies the open southeast aisle at approximately (1.5,-1.5,1.3) meters relative to the table center and faces northwest toward <Subject 1>. She is seated at the west end on screen-left, torso and head turned east toward <Subject 2>, with her gaze going screen-right. Her chin-length bob, natural eyebrow mark and dark red cardigan remain visible. His gray-clad shoulder and pale blue collar occupy only the extreme right foreground; his body remains at the east seat, and his shoulder does not obscure her face, hands or the recorder. The background shows the west green cabinet and only a geometrically plausible part of the north wall and window. The south door stays behind the camera and out of frame.\\nBoth remain seated on the same two chairs, feet on the floor, with neither changing seats or turning away. <Subject 1>'s two empty hands rest separately on the west table edge; <Subject 2>'s left hand rests on the east edge. There is exactly one small black rectangular audio recorder, about 10 by 3 by 1 centimeters, lying flat on the matte tabletop, long axis east-west and its single red indicator steadily lit. It has no readable display. Its center is 0.35 meters east and 0.12 meters south of the table center. His right fingertips rest on the tabletop three centimeters east of the recorder, separated from its casing. The recorder and both hands remain still until any explicitly directed action.\\nHold the initial pose for about one second. <Subject 1> (S1), using a clear low young-adult female Mandarin voice, measured and direct, says <d>[Chinese] 录音开着。你还要我关掉？</d> The statement about recording is a condition of this conversation, not a command to press a button. Finish speaking by about 4.5 seconds, close the mouth and hold eye contact for the remaining beat. Only speech-related lips, small facial tension and natural breathing change. The listener keeps a closed mouth and still hands. No control is pressed, and the indicator remains steadily red.\\nThe sole key is diffused cool-neutral daylight from the fixed high north window, above seated eye level. It softly illuminates the north-facing cheek, the upper knuckles and the recorder's top plane. Weak, slightly warm bounce from the south wall preserves detail on the shadow side without creating another hard shadow. Hair casts a gentle edge at the jaw, and sleeves retain soft folds. Small contact shadows attach hands and the recorder to the tabletop and extend toward the south in world space; the stationary recorder retains a stationary contact shadow. Keep source positions, exposure and white balance steady. Matte surfaces produce subdued highlights rather than flashes. Changing the viewpoint must not relocate the light to the camera side.\\nUse a 40 mm-equivalent lens at seated eye height, in a medium composition with enough depth of field for the featured face, hands and recorder to remain legible. Focus stays on the featured person's eyes without a focus pull. The camera remains fixed throughout; position, orientation, focal length and framing stay unchanged. The foreground shoulder remains a narrow edge element, not a moving wipe or obstruction. Keep the same single shot from beginning to end.\\nThe output is one full-frame scene, with no reference panels, additional people, automatic captions or decorative overlays. Preserve the settled end pose for the adjacent reverse-angle cut.\\n\\noverall_soundscape:\\nLow steady ventilation and distant, muffled room ambience, with subtle breaths and fabric noise. The stationary recorder produces no playback, beeps or repeated scrape. Keep the room tone unobtrusive beneath the voice.\\n\\nnon_diegetic_music:\\nN/A"
    },
    "class_type": "PrimitiveStringMultiline",
    "_meta": {
      "title": "Input Text (Prompt)"
    }
  },
  "139": {
    "inputs": {
      "image": "2636c786c4c0e6c33db28ba14bbe1c381ed4f7cbd8ae925b745e370640e55fea.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "141": {
    "inputs": {
      "max_resolution": 1024,
      "jpeg_quality": 80,
      "suppress_default_preview": True,
      "preview_frames": [
        "131",
        1
      ],
      "preview_fps": 12,
      "tiny_vae": "taeh3.safetensors",
      "model": [
        "178",
        0
      ]
    },
    "class_type": "ModelPreviewOverrideKJ",
    "_meta": {
      "title": "Model Preview Override KJ"
    }
  },
  "147": {
    "inputs": {
      "lora_name": "minimax_h3_ref2v_turbo_8step_v1.0_768p_comfyui_bf16.safetensors",
      "strength_model": 1.0000000000000002,
      "model": [
        "127",
        0
      ]
    },
    "class_type": "LoraLoaderModelOnly",
    "_meta": {
      "title": "Load LoRA"
    }
  },
  "149": {
    "inputs": {
      "shift_video": 12,
      "shift_audio": 3,
      "model": [
        "147",
        0
      ]
    },
    "class_type": "MiniMaxH3SigmaShift",
    "_meta": {
      "title": "ModelSamplingMiniMaxH3"
    }
  },
  "178": {
    "inputs": {
      "attention": "comfy kitchen attention",
      "model": [
        "149",
        0
      ]
    },
    "class_type": "ModelAttentionBackend",
    "_meta": {
      "title": "ModelAttentionBackend"
    }
  },
  "208": {
    "inputs": {
      "step": 6,
      "sigmas": [
        "254",
        0
      ]
    },
    "class_type": "SplitSigmas",
    "_meta": {
      "title": "SplitSigmas"
    }
  },
  "209": {
    "inputs": {
      "noise": [
        "129",
        0
      ],
      "guider": [
        "126",
        0
      ],
      "sampler": [
        "123",
        0
      ],
      "sigmas": [
        "208",
        1
      ],
      "latent_image": [
        "212",
        0
      ]
    },
    "class_type": "SamplerCustomAdvanced",
    "_meta": {
      "title": "SamplerCustomAdvanced"
    }
  },
  "211": {
    "inputs": {
      "av_latent": [
        "125",
        1
      ]
    },
    "class_type": "LTXVSeparateAVLatent",
    "_meta": {
      "title": "Separate AV Latent"
    }
  },
  "212": {
    "inputs": {
      "video_latent": [
        "263",
        0
      ],
      "audio_latent": [
        "211",
        1
      ]
    },
    "class_type": "LTXVConcatAVLatent",
    "_meta": {
      "title": "Concat AV Latent"
    }
  },
  "218": {
    "inputs": {
      "samples": [
        "209",
        0
      ],
      "vae": [
        "120",
        0
      ]
    },
    "class_type": "VAEDecodeAudio",
    "_meta": {
      "title": "VAE Decode Audio"
    }
  },
  "219": {
    "inputs": {
      "samples": [
        "209",
        0
      ],
      "vae": [
        "119",
        0
      ]
    },
    "class_type": "VAEDecode",
    "_meta": {
      "title": "VAE Decode"
    }
  },
  "254": {
    "inputs": {
      "extra_steps": 1,
      "start_at_sigma": 0.7,
      "end_at_sigma": 0,
      "spacing": "cosine",
      "sigmas": [
        "124",
        0
      ]
    },
    "class_type": "H3SigmaRefiner",
    "_meta": {
      "title": "H3 Sigma Refiner"
    }
  },
  "256": {
    "inputs": {
      "image": "07d2e1d22673808899bba100354351b0d4b5b723a10358c7a9ffe92ec0c98ddc.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "257": {
    "inputs": {
      "image": "56a596334282d0057a0847e7a1f2714e8aa27725718b5a162e3ac33c02e42b17.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "258": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "259": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "260": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "263": {
    "inputs": {
      "model_name": "minimax_h3_latent_upscaler_3d_fp16.safetensors",
      "mode": "scale by multiplier",
      "mode.scale": 2,
      "align": 32,
      "device": "cuda",
      "precision": "fp16",
      "enable_chunking": True,
      "latent": [
        "211",
        0
      ]
    },
    "class_type": "MinimaxH3LatentUpscaler3D",
    "_meta": {
      "title": "Minimax H3 Latent Upscaler (3D)"
    }
  },
  "271": {
    "inputs": {
      "frame_rate": 24,
      "loop_count": 0,
      "filename_prefix": "第二次采样",
      "format": "video/h264-mp4",
      "pix_fmt": "yuv420p",
      "crf": 19,
      "save_metadata": True,
      "trim_to_audio": False,
      "pingpong": False,
      "save_output": True,
      "no_preview": False,
      "images": [
        "219",
        0
      ],
      "audio": [
        "218",
        0
      ]
    },
    "class_type": "VHS_VideoCombine",
    "_meta": {
      "title": "Video Combine 🎥🅥🅗🅢"
    }
  },
  "272": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "273": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "274": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "275": {
    "inputs": {
      "audio": "0ea9bca3948a0baf7983804066a8884203e6452b1c37a109bf6e5dc24e616996.flac",
      "audioUI": ""
    },
    "class_type": "LoadAudio",
    "_meta": {
      "title": "Load Audio"
    }
  }
}

# minimax_h3 1张图片参考
minimax_h3_1_image_json = {
  "115": {
    "inputs": {
      "aspect_ratio": "16:9 (Widescreen)",
      "megapixels": 0.5,
      "multiple": 32
    },
    "class_type": "ResolutionSelector",
    "_meta": {
      "title": "PASS1 / 16:9 / 0.5MP"
    }
  },
  "119": {
    "inputs": {
      "vae_name": "minimax_h3_video_vae_fp16.safetensors"
    },
    "class_type": "VAELoader",
    "_meta": {
      "title": "Load VAE"
    }
  },
  "120": {
    "inputs": {
      "vae_name": "minimax_h3_audio_vae_fp32.safetensors"
    },
    "class_type": "VAELoader",
    "_meta": {
      "title": "Load VAE"
    }
  },
  "123": {
    "inputs": {
      "sampler_name": "euler"
    },
    "class_type": "KSamplerSelect",
    "_meta": {
      "title": "KSamplerSelect"
    }
  },
  "124": {
    "inputs": {
      "scheduler": "simple",
      "steps": 10,
      "denoise": 1,
      "model": [
        "141",
        0
      ]
    },
    "class_type": "BasicScheduler",
    "_meta": {
      "title": "BasicScheduler"
    }
  },
  "125": {
    "inputs": {
      "noise": [
        "129",
        0
      ],
      "guider": [
        "126",
        0
      ],
      "sampler": [
        "123",
        0
      ],
      "sigmas": [
        "208",
        0
      ],
      "latent_image": [
        "136",
        1
      ]
    },
    "class_type": "SamplerCustomAdvanced",
    "_meta": {
      "title": "SamplerCustomAdvanced"
    }
  },
  "126": {
    "inputs": {
      "model": [
        "141",
        0
      ],
      "conditioning": [
        "136",
        0
      ]
    },
    "class_type": "BasicGuider",
    "_meta": {
      "title": "Basic Guider"
    }
  },
  "127": {
    "inputs": {
      "unet_name": "minimax_h3_hybrid_fl2va_ref2va_b25-49-int8.safetensors",
      "weight_dtype": "default"
    },
    "class_type": "UNETLoader",
    "_meta": {
      "title": "Load Diffusion Model"
    }
  },
  "128": {
    "inputs": {
      "clip_name": "qwen3vl_32b_minimax_h3_int8_convrot.safetensors",
      "type": "minimax",
      "device": "default"
    },
    "class_type": "CLIPLoader",
    "_meta": {
      "title": "Load CLIP"
    }
  },
  "129": {
    "inputs": {
      "noise_seed": 999
    },
    "class_type": "RandomNoise",
    "_meta": {
      "title": "RandomNoise"
    }
  },
  "131": {
    "inputs": {
      "expression": "max(5, round(a * 24)) + (5 - (max(5, round(a * 24)) % 17)) % 17",
      "values.a": [
        "132",
        0
      ]
    },
    "class_type": "ComfyMathExpression",
    "_meta": {
      "title": "Math Expression"
    }
  },
  "132": {
    "inputs": {
      "value": 6
    },
    "class_type": "PrimitiveFloat",
    "_meta": {
      "title": "Float (Duration)"
    }
  },
  "136": {
    "inputs": {
      "prompt": [
        "138",
        0
      ],
      "width": [
        "115",
        0
      ],
      "height": [
        "115",
        1
      ],
      "length": [
        "131",
        1
      ],
      "task_type": "auto",
      "audio_mode": "native",
      "audio_denoise_strength": 1,
      "add_source_as_reference": False,
      "prompt_primary_audio_ordinal": 0,
      "strict_prompt_tags": True,
      "ref_image_size": "match",
      "reference_video_policy": "official_2_to_15s",
      "allow_above_reference_area": True,
      "clip": [
        "128",
        0
      ],
      "video_vae": [
        "119",
        0
      ],
      "audio_vae": [
        "120",
        0
      ],
      "ref_images.ref_image_0": [
        "139",
        0
      ]
    },
    "class_type": "MiniMaxH3AudioConditioningT8",
    "_meta": {
      "title": "T8 条件节点｜通用模式"
    }
  },
  "138": {
    "inputs": {
      "value": "subject_definitions:\\n<Subject 1> is Lin Che from <Picture 1>, a 29-year-old Chinese woman with a chin-length black bob, a small mole at the outer end of her left eyebrow, a dark red buttoned knitted cardigan over a white crew-neck top and black trousers. Preserve her facial identity, natural skin and wardrobe; the three standing views do not dictate her seated performance.\\n<Subject 2> is Chen Li from <Picture 2>, a 48-year-old Chinese man with a square face, short black hair graying at the temples, a slight gap in his right eyebrow, a medium-gray knitted cardigan over a pale blue shirt and dark gray trousers. Preserve his face, age, hair and clothing, not the reference pose.\\n<Subject 3> is the same empty meeting room from <Picture 3>: a matte light-gray rectangular table with its long axis east-west, one chair at each east and west short end, a closed high frosted window in the north wall, a low dark-green six-cubby cabinet against the west wall and a closed brown door in the south wall. Preserve the world-space layout and matte surfaces. Omit the four-view borders, reference viewpoints and incidental objects; the room contains only the two directed people and the one directed recorder.\\n\\nsummary:\\n[reference generation] A 6-second continuous live-action medium shot in <Subject 3>. Lin Che establishes that the recorder is already running and challenges Chen Li to speak on record. The three pictures supply identity and room design, with newly directed framing rather than exact endpoints.\\n\\nretention_analysis:\\n<Subject 1> (appears in [Shot 1]): fully_preserved - Keep Lin Che's identity, bob, dark red cardigan and white inner top while directing the specified seated performance.\\n<Subject 2> (appears in [Shot 1]): fully_preserved - Keep Chen Li's identity, gray temples, gray cardigan and pale blue shirt; the directed seated pose replaces the standing reference.\\n<Subject 3> (appears in [Shot 1]): partially_preserved - Keep the fixed room topology, north-window light, west cabinet and table material; omit multi-view panels and reference framing. The initial camera composition is newly directed.\\n\\ndetailed_description:\\nThe target video is a restrained contemporary Chinese live-action suspense drama, with natural skin texture, readable faces and softly lit matte surfaces.\\n[Shot 1] The camera occupies the open southeast aisle at approximately (1.5,-1.5,1.3) meters relative to the table center and faces northwest toward <Subject 1>. She is seated at the west end on screen-left, torso and head turned east toward <Subject 2>, with her gaze going screen-right. Her chin-length bob, natural eyebrow mark and dark red cardigan remain visible. His gray-clad shoulder and pale blue collar occupy only the extreme right foreground; his body remains at the east seat, and his shoulder does not obscure her face, hands or the recorder. The background shows the west green cabinet and only a geometrically plausible part of the north wall and window. The south door stays behind the camera and out of frame.\\nBoth remain seated on the same two chairs, feet on the floor, with neither changing seats or turning away. <Subject 1>'s two empty hands rest separately on the west table edge; <Subject 2>'s left hand rests on the east edge. There is exactly one small black rectangular audio recorder, about 10 by 3 by 1 centimeters, lying flat on the matte tabletop, long axis east-west and its single red indicator steadily lit. It has no readable display. Its center is 0.35 meters east and 0.12 meters south of the table center. His right fingertips rest on the tabletop three centimeters east of the recorder, separated from its casing. The recorder and both hands remain still until any explicitly directed action.\\nHold the initial pose for about one second. <Subject 1> (S1), using a clear low young-adult female Mandarin voice, measured and direct, says <d>[Chinese] 录音开着。你还要我关掉？</d> The statement about recording is a condition of this conversation, not a command to press a button. Finish speaking by about 4.5 seconds, close the mouth and hold eye contact for the remaining beat. Only speech-related lips, small facial tension and natural breathing change. The listener keeps a closed mouth and still hands. No control is pressed, and the indicator remains steadily red.\\nThe sole key is diffused cool-neutral daylight from the fixed high north window, above seated eye level. It softly illuminates the north-facing cheek, the upper knuckles and the recorder's top plane. Weak, slightly warm bounce from the south wall preserves detail on the shadow side without creating another hard shadow. Hair casts a gentle edge at the jaw, and sleeves retain soft folds. Small contact shadows attach hands and the recorder to the tabletop and extend toward the south in world space; the stationary recorder retains a stationary contact shadow. Keep source positions, exposure and white balance steady. Matte surfaces produce subdued highlights rather than flashes. Changing the viewpoint must not relocate the light to the camera side.\\nUse a 40 mm-equivalent lens at seated eye height, in a medium composition with enough depth of field for the featured face, hands and recorder to remain legible. Focus stays on the featured person's eyes without a focus pull. The camera remains fixed throughout; position, orientation, focal length and framing stay unchanged. The foreground shoulder remains a narrow edge element, not a moving wipe or obstruction. Keep the same single shot from beginning to end.\\nThe output is one full-frame scene, with no reference panels, additional people, automatic captions or decorative overlays. Preserve the settled end pose for the adjacent reverse-angle cut.\\n\\noverall_soundscape:\\nLow steady ventilation and distant, muffled room ambience, with subtle breaths and fabric noise. The stationary recorder produces no playback, beeps or repeated scrape. Keep the room tone unobtrusive beneath the voice.\\n\\nnon_diegetic_music:\\nN/A"
    },
    "class_type": "PrimitiveStringMultiline",
    "_meta": {
      "title": "Input Text (Prompt)"
    }
  },
  "139": {
    "inputs": {
      "image": "2636c786c4c0e6c33db28ba14bbe1c381ed4f7cbd8ae925b745e370640e55fea.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "141": {
    "inputs": {
      "max_resolution": 1024,
      "jpeg_quality": 80,
      "suppress_default_preview": True,
      "preview_frames": [
        "131",
        1
      ],
      "preview_fps": 12,
      "tiny_vae": "taeh3.safetensors",
      "model": [
        "178",
        0
      ]
    },
    "class_type": "ModelPreviewOverrideKJ",
    "_meta": {
      "title": "Model Preview Override KJ"
    }
  },
  "147": {
    "inputs": {
      "lora_name": "minimax_h3_ref2v_turbo_8step_v1.0_768p_comfyui_bf16.safetensors",
      "strength_model": 1.0000000000000002,
      "model": [
        "127",
        0
      ]
    },
    "class_type": "LoraLoaderModelOnly",
    "_meta": {
      "title": "Load LoRA"
    }
  },
  "149": {
    "inputs": {
      "shift_video": 12,
      "shift_audio": 3,
      "model": [
        "147",
        0
      ]
    },
    "class_type": "MiniMaxH3SigmaShift",
    "_meta": {
      "title": "ModelSamplingMiniMaxH3"
    }
  },
  "178": {
    "inputs": {
      "attention": "comfy kitchen attention",
      "model": [
        "149",
        0
      ]
    },
    "class_type": "ModelAttentionBackend",
    "_meta": {
      "title": "ModelAttentionBackend"
    }
  },
  "208": {
    "inputs": {
      "step": 6,
      "sigmas": [
        "254",
        0
      ]
    },
    "class_type": "SplitSigmas",
    "_meta": {
      "title": "SplitSigmas"
    }
  },
  "209": {
    "inputs": {
      "noise": [
        "129",
        0
      ],
      "guider": [
        "126",
        0
      ],
      "sampler": [
        "123",
        0
      ],
      "sigmas": [
        "208",
        1
      ],
      "latent_image": [
        "212",
        0
      ]
    },
    "class_type": "SamplerCustomAdvanced",
    "_meta": {
      "title": "SamplerCustomAdvanced"
    }
  },
  "211": {
    "inputs": {
      "av_latent": [
        "125",
        1
      ]
    },
    "class_type": "LTXVSeparateAVLatent",
    "_meta": {
      "title": "Separate AV Latent"
    }
  },
  "212": {
    "inputs": {
      "video_latent": [
        "263",
        0
      ],
      "audio_latent": [
        "211",
        1
      ]
    },
    "class_type": "LTXVConcatAVLatent",
    "_meta": {
      "title": "Concat AV Latent"
    }
  },
  "218": {
    "inputs": {
      "samples": [
        "209",
        0
      ],
      "vae": [
        "120",
        0
      ]
    },
    "class_type": "VAEDecodeAudio",
    "_meta": {
      "title": "VAE Decode Audio"
    }
  },
  "219": {
    "inputs": {
      "samples": [
        "209",
        0
      ],
      "vae": [
        "119",
        0
      ]
    },
    "class_type": "VAEDecode",
    "_meta": {
      "title": "VAE Decode"
    }
  },
  "254": {
    "inputs": {
      "extra_steps": 1,
      "start_at_sigma": 0.7,
      "end_at_sigma": 0,
      "spacing": "cosine",
      "sigmas": [
        "124",
        0
      ]
    },
    "class_type": "H3SigmaRefiner",
    "_meta": {
      "title": "H3 Sigma Refiner"
    }
  },
  "256": {
    "inputs": {
      "image": "07d2e1d22673808899bba100354351b0d4b5b723a10358c7a9ffe92ec0c98ddc.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "257": {
    "inputs": {
      "image": "56a596334282d0057a0847e7a1f2714e8aa27725718b5a162e3ac33c02e42b17.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "258": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "259": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "260": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "263": {
    "inputs": {
      "model_name": "minimax_h3_latent_upscaler_3d_fp16.safetensors",
      "mode": "scale by multiplier",
      "mode.scale": 2,
      "align": 32,
      "device": "cuda",
      "precision": "fp16",
      "enable_chunking": True,
      "latent": [
        "211",
        0
      ]
    },
    "class_type": "MinimaxH3LatentUpscaler3D",
    "_meta": {
      "title": "Minimax H3 Latent Upscaler (3D)"
    }
  },
  "271": {
    "inputs": {
      "frame_rate": 24,
      "loop_count": 0,
      "filename_prefix": "第二次采样",
      "format": "video/h264-mp4",
      "pix_fmt": "yuv420p",
      "crf": 19,
      "save_metadata": True,
      "trim_to_audio": False,
      "pingpong": False,
      "save_output": True,
      "no_preview": False,
      "images": [
        "219",
        0
      ],
      "audio": [
        "218",
        0
      ]
    },
    "class_type": "VHS_VideoCombine",
    "_meta": {
      "title": "Video Combine 🎥🅥🅗🅢"
    }
  },
  "272": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "273": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "274": {
    "inputs": {
      "image": "pasted/ddeed433abbc6923f08a9f3c679480c66149962653db599cac6cedf429318a8b.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "275": {
    "inputs": {
      "audio": "0ea9bca3948a0baf7983804066a8884203e6452b1c37a109bf6e5dc24e616996.flac",
      "audioUI": ""
    },
    "class_type": "LoadAudio",
    "_meta": {
      "title": "Load Audio"
    }
  }
}
