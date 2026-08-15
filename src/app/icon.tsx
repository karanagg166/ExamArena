import { ImageResponse } from "next/og";

export const size = {
  width: 32,
  height: 32,
};
export const contentType = "image/png";

export default function Icon() {
  return new ImageResponse(
    (
      <div
        style={{
          fontSize: 20,
          background: "linear-gradient(135deg, #6366F1 0%, #4338CA 100%)",
          width: "100%",
          height: "100%",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          color: "white",
          borderRadius: 8,
          boxShadow: "0 2px 8px rgba(79, 70, 229, 0.4)",
        }}
      >
        🎓
      </div>
    ),
    {
      ...size,
    },
  );
}
