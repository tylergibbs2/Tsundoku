interface IonIconParams {
  name?: string;
  className?: string;
  src?: string;
  ios?: string;
  md?: string;
  size?: string;
}

export const IonIcon = ({
  name,
  className,
  src,
  ios,
  md,
  size,
}: IonIconParams) => {
  return (
    <>
      {/* @ts-ignore */}
      <ion-icon
        name={name}
        className={className}
        src={src}
        ios={ios}
        md={md}
        size={size}
      >
        {/* @ts-ignore */}
      </ion-icon>
    </>
  );
};
