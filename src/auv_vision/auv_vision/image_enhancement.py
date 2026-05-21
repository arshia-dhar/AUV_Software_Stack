import cv2
import numpy as np


class VisionEnhancerCUDA:
    def __init__(self, gamma=1.5, clahe_clip=2.0, clahe_tile=(8, 8)):
        """Initialize the L-Channel Injection pipeline."""

        # 1. CPU Precompute Gamma LUT
        inv_gamma = 1.0 / gamma
        self.lut = np.array(
            [((i / 255.0) ** inv_gamma) * 255 for i in np.arange(0, 256)]).astype("uint8")

        # 2. GPU Precompute CLAHE object
        self.clahe_cuda = cv2.cuda.createCLAHE(
            clipLimit=clahe_clip, tileGridSize=clahe_tile)

        # 3. GPU Memory allocation for the L-channel ONLY
        self.gpu_l = cv2.cuda_GpuMat()
        self.stream = cv2.cuda_Stream()

    def apply_gray_world_cpu(self, frame):
        """Standard CPU Gray World."""
        mean_val = cv2.mean(frame)
        avg_b, avg_g, avg_r = mean_val[0], mean_val[1], mean_val[2]
        avg_gray = (avg_b + avg_g + avg_r) / 3.0

        scale_b = avg_gray / avg_b if avg_b > 0 else 1.0
        scale_g = avg_gray / avg_g if avg_g > 0 else 1.0
        scale_r = avg_gray / avg_r if avg_r > 0 else 1.0

        b, g, r = cv2.split(frame)
        b = cv2.convertScaleAbs(b, alpha=scale_b)
        g = cv2.convertScaleAbs(g, alpha=scale_g)
        r = cv2.convertScaleAbs(r, alpha=scale_r)

        return cv2.merge((b, g, r))

    def process_frame(self, frame):
        """The optimized, memory-safe master pipeline."""

        # Fix color cast and lift shadows
        color_fixed = self.apply_gray_world_cpu(frame)
        brightened = cv2.LUT(color_fixed, self.lut)

        # Convert to LAB and split directly on the CPU (Zero binding bugs here)
        lab = cv2.cvtColor(brightened, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)

        # Upload ONLY the 1-channel Lightness data
        self.gpu_l.upload(l, self.stream)

        # Apply CUDA CLAHE
        l_enhanced_gpu = self.clahe_cuda.apply(self.gpu_l, self.stream)

        # Download the finished structure channel back to the CPU
        l_enhanced = l_enhanced_gpu.download(self.stream)

        # Boost saturation on the color channels safely
        saturation_boost = 1.3
        beta = 128 * (1.0 - saturation_boost)
        a_boosted = cv2.convertScaleAbs(a, alpha=saturation_boost, beta=beta)
        b_boosted = cv2.convertScaleAbs(b, alpha=saturation_boost, beta=beta)

        # Merge and convert back to BGR
        merged = cv2.merge((l_enhanced, a_boosted, b_boosted))
        final_frame = cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)

        return final_frame
